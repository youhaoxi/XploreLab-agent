""" 
Simple agent with tools -- built-in toolkits, MCPs
"""
import logging
from typing import Callable
from contextlib import AsyncExitStack
from agents import Agent, Tool
from agents.mcp import MCPServerStdio, MCPServer, MCPUtil

from .base import UTUAgentBase
from ..utils import AgentsUtils
from ..tools import TOOLKIT_MAP, AsyncBaseToolkit
from ..config import ToolkitConfig

logger = logging.getLogger("utu")


class UTUSimpleAgent(UTUAgentBase):
    _mcp_servers: list[MCPServer] = []
    _toolkits: list[AsyncBaseToolkit] = []
    
    def __init__(
        self,
        config_name: str = "default",
        name: str = None,
        instructions: str = None,
        *args, **kwargs
    ):
        super().__init__(config_name, *args, **kwargs)
        # override config
        if name: self.config.agent.name = name
        if instructions: self.config.agent.instructions = instructions
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def build(self):
        """ Build the agent """
        model = AgentsUtils.get_agents_model(**self.config.model.model_dump())
        tools = await self.load_tools()
        agent = Agent[self.context](
            name=self.name,
            instructions=await self.build_instructions(),
            model=model,
            tools=tools,
            # mcp_servers  # manually setup mcp servers & tools
        )
        self.set_agent(agent)
    
    async def cleanup(self):
        """ Cleanup """
        logger.info("Cleaning up... (MCP servers)")
        await self._exit_stack.aclose()
        self._mcp_servers = []

    async def load_tools(self) -> list[Tool]:
        """ Load tools from config. You can override this method to load tools from other sources. """
        tools_list: list[Tool] = []
        for toolkit_name, toolkit_config in self.config.toolkits.items():
            # TODO: handle duplicate tool names
            if toolkit_config.mode == "mcp":
                await self._load_mcp_server(toolkit_config)
            elif toolkit_config.mode == "builtin":
                toolkit = await self._load_builtin_toolkit(toolkit_config)
                tools_list.extend(await toolkit.get_tools_in_agents())
            else:
                raise ValueError(f"Unknown toolkit mode: {toolkit_config.mode}")
        # use `MCPUtil` to get tools from mcp servers
        if self._mcp_servers:
            tools_list.extend(await MCPUtil.get_all_function_tools(self._mcp_servers, convert_schemas_to_strict=False))
        tool_names = [tool.name for tool in tools_list]
        logger.info(f"Loaded {len(tool_names)} tools: {tool_names}")
        return tools_list

    async def build_instructions(self) -> str | Callable:
        """ Build instructions from config. You can override this method to build customized instructions. """
        return self.config.agent.instructions

    async def _load_mcp_server(self, toolkit_config: ToolkitConfig) -> MCPServer:
        logger.info(f"Loading MCP server `{toolkit_config.name}` with params {toolkit_config.config}")
        server = await self._exit_stack.enter_async_context(
            MCPServerStdio(  # FIXME: support other types of servers
                name=toolkit_config.name,
                params=toolkit_config.config,
                client_session_timeout_seconds=20,
            )
        )
        self._mcp_servers.append(server)
        return server

    async def _load_builtin_toolkit(self, toolkit_config: ToolkitConfig) -> AsyncBaseToolkit:
        logger.info(f"Loading builtin toolkit `{toolkit_config.name}` with config {toolkit_config.config}")
        assert toolkit_config.name in TOOLKIT_MAP, f"Unknown toolkit name: {toolkit_config.name}"
        toolkit = TOOLKIT_MAP[toolkit_config.name](
            config=toolkit_config,
            activated_tools=toolkit_config.activated_tools,
        )
        self._toolkits.append(toolkit)
        return toolkit
