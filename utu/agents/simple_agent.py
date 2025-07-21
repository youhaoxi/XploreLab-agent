""" 
- [ ] env https://github.com/RAGEN-AI/RAGEN/blob/main/ragen/env/base.py (gym like)
"""

import logging
from contextlib import AsyncExitStack

from agents import Tool, TContext, RunResult, RunResultStreaming, Agent, TResponseInputItem, Runner, RunHooks, RunConfig
from agents.tracing import trace, Trace, gen_trace_id
from agents.mcp import MCPServerStdio, MCPServer

from ..config import AgentConfig, ToolkitConfig, ConfigLoader
from ..tools import AsyncBaseToolkit, TOOLKIT_MAP
from ..utils import AgentsUtils
from ..context import BaseContextManager, CONTEXT_MANAGER_MAP

logger = logging.getLogger("utu")


class RunnerMixin:
    config: AgentConfig = None
    current_agent: Agent[TContext] = None
    input_items: list[TResponseInputItem] = []
    context_manager: BaseContextManager = None
    # tracer: Trace = None
    trace_id: str = None
    _run_hooks: RunHooks = None

    # def setup_tracer(self):
    #     if self.tracer: return
    #     self.tracer = trace(
    #         workflow_name=self.config.agent.name,  # FIXME: multi-agent?
    #         trace_id=gen_trace_id(),
    #         # metadata={
    #         #     "config": str(self.config.model_dump())
    #         # }  # FIXME: str too long for phoenix
    #     )
    #     self.tracer.start(mark_as_current=True)
    #     print(f"> trace_id: {self.tracer.trace_id}")
    #     # TODO: get otel trace_id --> set same as self.tracer.trace_id
    #     # print(f"> otel trace_id: {otel_span.get_span_context().trace_id}")

    def _get_run_config(self) -> RunConfig:
        self.trace_id = gen_trace_id()
        logger.info(f"> trace_id: {self.trace_id}")
        run_config = RunConfig(
            model_settings=self.config.model_settings,
            trace_id=self.trace_id,
            workflow_name=self.config.agent.name,
        )
        return run_config

    def _get_context(self) -> dict:
        return {
            "context_manager": self.context_manager,
        }

    # wrap `Runner` apis in @openai-agents
    async def run(self, input: str | list[TResponseInputItem]) -> RunResult:
        return await Runner.run(
            self.current_agent, 
            input, 
            context=self._get_context(),
            max_turns=self.config.max_turns,
            hooks=self._run_hooks,
            run_config=self._get_run_config(), 
        )

    def run_streamed(self, input: str | list[TResponseInputItem]) -> RunResultStreaming:
        return Runner.run_streamed(
            self.current_agent, 
            input, 
            context=self._get_context(),
            max_turns=self.config.max_turns,
            hooks=self._run_hooks,
            run_config=self._get_run_config(), 
        )

    # util apis
    async def chat(self, input: str) -> RunResult:
        # TODO: support multi-modal input -- `def add_input(...)`
        # TODO: set "session-level" tracing for multi-turn chat
        self.input_items.append({"content": input, "role": "user"})
        run_result = await self.run(self.input_items)
        AgentsUtils.print_new_items(run_result.new_items)
        self.input_items = run_result.to_input_list()
        self.current_agent = run_result.last_agent
        return run_result
    
    async def chat_streamed(self, input: str):
        self.input_items.append({"content": input, "role": "user"})
        run_result_streaming = self.run_streamed(self.input_items)
        await AgentsUtils.print_stream_events(run_result_streaming.stream_events())
        self.input_items = run_result_streaming.to_input_list()
        self.current_agent = run_result_streaming.last_agent

    def set_run_hooks(self, run_hooks: RunHooks):
        self._run_hooks = run_hooks


class SimpleAgent(RunnerMixin):
    config: AgentConfig = None
    current_agent: Agent[TContext] = None
    input_items: list[TResponseInputItem] = []
    context_manager: BaseContextManager = None
    
    _mcp_servers: list[MCPServer] = []
    _toolkits: list[AsyncBaseToolkit] = []
    _tools: list[Tool] = []

    def __init__(
        self, 
        config: AgentConfig|str,
        *,
        name: str = None,
        instructions: str = None,
        tools: list[Tool] = None,
    ):
        if isinstance(config, str):
            config = ConfigLoader.load_agent_config(config)
        if name: config.agent.name = name
        if instructions: config.agent.instructions = instructions
        self.config = config

        if tools: self._tools = tools
        
        self._build_context_manager()
        # self.setup_tracer()
        self._mcps_exit_stack = AsyncExitStack()
        self._tools_exit_stack = AsyncExitStack()

    def _build_context_manager(self):
        if (not self.config.context_manager) or (not self.config.context_manager.name):
            self.context_manager = CONTEXT_MANAGER_MAP["dummy"]()
        else:
            self.context_manager = CONTEXT_MANAGER_MAP[self.config.context_manager.name](
                self.config.context_manager.config
            )

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def build(self):
        """ Build the agent """
        model = AgentsUtils.get_agents_model(**self.config.model.model_dump())
        tools = self._tools if self._tools else await self.get_tools()
        self.current_agent = Agent(
            name=self.config.agent.name,
            instructions=await self.build_instructions(),
            model=model,
            tools=tools,
            mcp_servers=self._mcp_servers
        )

    async def cleanup(self):
        """ Cleanup """
        logger.info("Cleaning up... (MCP servers)")
        await self._mcps_exit_stack.aclose()
        self._mcp_servers = []
        logger.info("Cleaning up... (tools)")
        await self._tools_exit_stack.aclose()
        self._toolkits = []

    async def build_instructions(self) -> str:
        """ Build instructions from config. You can override this method to build customized instructions. """
        return self.config.agent.instructions

    async def get_tools(self) -> list[Tool]:
        tools_list: list[Tool] = []
        # TODO: handle duplicate tool names
        for toolkit_name, toolkit_config in self.config.toolkits.items():
            if toolkit_config.mode == "mcp":
                await self._load_mcp_server(toolkit_config)
            elif toolkit_config.mode == "builtin":
                toolkit = await self._load_toolkit(toolkit_config)
                tools_list.extend(await toolkit.get_tools_in_agents())
            else:
                raise ValueError(f"Unknown toolkit mode: {toolkit_config.mode}")
        # # use `MCPUtil` to get tools from mcp servers
        # if self._mcp_servers:
        #     if self.current_agent is None: raise ValueError("MCP tools are only accessible after agent is inited")
        #     tools_list.extend(await MCPUtil.get_all_function_tools(
        #         self._mcp_servers, convert_schemas_to_strict=False, 
        #         run_context=RunContextWrapper(context=self.context), agent=self.current_agent))
        tool_names = [tool.name for tool in tools_list]
        logger.info(f"Loaded {len(tool_names)} tools: {tool_names}")
        return tools_list

    # async def get_state(self) -> str:
    #     return ""

    async def _load_toolkit(self, toolkit_config: ToolkitConfig) -> AsyncBaseToolkit:
        logger.info(f"Loading builtin toolkit `{toolkit_config.name}` with config {toolkit_config}")
        toolkit = await self._tools_exit_stack.enter_async_context(
            TOOLKIT_MAP[toolkit_config.name](toolkit_config)
        )
        self._toolkits.append(toolkit)
        return toolkit

    async def _load_mcp_server(self, toolkit_config: ToolkitConfig) -> MCPServer:
        logger.info(f"Loading MCP server `{toolkit_config.name}` with params {toolkit_config.config}")
        server = await self._mcps_exit_stack.enter_async_context(
            MCPServerStdio(  # FIXME: support other types of servers
                name=toolkit_config.name,
                params=toolkit_config.config,
                client_session_timeout_seconds=20,
            )
        )
        self._mcp_servers.append(server)
        return server
