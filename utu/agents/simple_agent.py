from contextlib import AsyncExitStack

from agents import Tool, TContext, RunResult, RunResultStreaming, Agent, TResponseInputItem, Runner, RunHooks, RunConfig
from agents.tracing import gen_trace_id, get_current_trace
from agents.mcp import MCPServerStdio, MCPServer

from ..config import AgentConfig, ToolkitConfig, ConfigLoader
from ..tools import AsyncBaseToolkit, TOOLKIT_MAP
from ..utils import AgentsUtils, get_logger
from ..context import BaseContextManager, build_context_manager
from ..env import get_env, BaseEnv
from ..tracing import setup_tracing

logger = get_logger(__name__)


class SimpleAgent:
    """A simple agent with env, tools, mcps, and context manager, wrapped on openai-agents."""

    def __init__(
        self, 
        config: AgentConfig|str,
        *,
        name: str = None,
        instructions: str = None,
        tools: list[Tool] = None,
    ):
        self.config = self._process_config(config, name, instructions)
        self.tools: list[Tool] = tools or []
        self.context_manager: BaseContextManager = None
        self.env: BaseEnv = None
        self.current_agent: Agent[TContext] = None
        self.input_items: list[TResponseInputItem] = []

        self._run_hooks: RunHooks = None
        self._mcp_servers: list[MCPServer] = []
        self._toolkits: list[AsyncBaseToolkit] = []
        self._trace_id: str = None
        self._mcps_exit_stack = AsyncExitStack()
        self._tools_exit_stack = AsyncExitStack()

    def _process_config(self, config: AgentConfig|str, name: str = None, instructions: str = None) -> AgentConfig:
        if isinstance(config, str):
            config = ConfigLoader.load_agent_config(config)
        if name: config.agent.name = name
        if instructions: config.agent.instructions = instructions
        return config

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def build(self):
        """ Build the agent """
        self.env = await get_env(self.config, self._trace_id)  # FIXME: trace_id
        await self.env.build()
        model = AgentsUtils.get_agents_model(**self.config.model.model_provider.model_dump())
        self.current_agent = Agent(
            name=self.config.agent.name,
            instructions=await self.build_instructions(),
            model=model,
            tools=await self.get_tools(),
            mcp_servers=self._mcp_servers
        )
        self.context_manager = build_context_manager(self.config)

    async def cleanup(self):
        """ Cleanup """
        logger.info("Cleaning up MCP servers...")
        await self._mcps_exit_stack.aclose()
        self._mcp_servers = []
        logger.info("Cleaning up tools...")
        await self._tools_exit_stack.aclose()
        self._toolkits = []
        logger.info("Cleaning up env...")
        await self.env.cleanup()

    async def build_instructions(self) -> str:
        """ Build instructions from config. You can override this method to build customized instructions. """
        sp_prefix = self.env.get_sp_prefix()
        return sp_prefix + self.config.agent.instructions

    async def get_tools(self) -> list[Tool]:
        if self.tools:
            return self.tools
        
        tools_list: list[Tool] = []
        tools_list += await self.env.get_tools()  # add env tools
        # TODO: handle duplicate tool names
        for toolkit_name, toolkit_config in self.config.toolkits.items():
            if toolkit_config.mode == "mcp":
                await self._load_mcp_server(toolkit_config)
            elif toolkit_config.mode == "builtin":
                toolkit = await self._load_toolkit(toolkit_config)
                tools_list.extend(await toolkit.get_tools_in_agents())
            else:
                raise ValueError(f"Unknown toolkit mode: {toolkit_config.mode}")
        tool_names = [tool.name for tool in tools_list]
        logger.info(f"Loaded {len(tool_names)} tools: {tool_names}")
        self.tools = tools_list
        return tools_list

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

    # RunnerMixin apis
    def _get_trace_id(self) -> str:
        if not self._trace_id:
            current_trace = get_current_trace()
            self._trace_id = gen_trace_id() if current_trace is None else current_trace.trace_id
        logger.info(f"> trace_id: {self._trace_id}")
        return self._trace_id

    def _get_run_config(self) -> RunConfig:
        run_config = RunConfig(
            model=self.current_agent.model,
            model_settings=self.config.model.model_settings,
            trace_id=self._get_trace_id(),
            workflow_name=self.config.agent.name,
        )
        return run_config

    def _get_context(self) -> dict:
        return {
            "context_manager": self.context_manager,
            "env": self.env,
        }

    # wrap `Runner` apis in @openai-agents
    async def run(self, input: str | list[TResponseInputItem], trace_id: str = None) -> RunResult:
        setup_tracing()
        if trace_id: self._trace_id = trace_id
        return await Runner.run(
            self.current_agent, 
            input, 
            context=self._get_context(),
            max_turns=self.config.max_turns,
            hooks=self._run_hooks,
            run_config=self._get_run_config(), 
        )

    def run_streamed(self, input: str | list[TResponseInputItem], trace_id: str = None) -> RunResultStreaming:
        setup_tracing()
        if trace_id: self._trace_id = trace_id
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
        # WIP
        self._run_hooks = run_hooks
