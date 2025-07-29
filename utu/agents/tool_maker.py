import logging
import json
from typing import Any

from agents import RunHooks, RunContextWrapper, TContext, Agent, Tool
from agents.mcp import MCPServerStdioParams, MCPServerStdio, MCPUtil

from .base import UTUContext
from .simple import UTUSimpleAgent
from ..tool_maker import make_tool

logger = logging.getLogger(__name__)


class ToolMakerRunHooks(RunHooks):
    async def on_tool_end(self, context: RunContextWrapper[UTUContext], agent: Agent[UTUContext], tool: Tool, result: str) -> None:
        """Postprocess of ToolMaker tool: start the MCP server and add tools"""
        if tool.name != "make_tool": return
        logger.info(f"[hook] Processing made tool: {result}")
        if isinstance(result, str):
            try:
                result = json.loads(result)  # FIXME: validate by MCPServerStdioParams
            except Exception as e:
                raise ValueError(f"Invalid tool made: {result}! Exception: {e}")
        utu_context = context.context
        server = await utu_context.exit_stack.enter_async_context(
            MCPServerStdio(
                # name?
                params=result,
                client_session_timeout_seconds=20,
            )
        )
        utu_context.dynamic_mcp_servers.append(server)
        # add tools TODO: move tools to Context
        new_tools = await MCPUtil.get_all_function_tools([server], convert_schemas_to_strict=False)
        utu_context.current_agent.tools.extend(new_tools)
        logger.info(f"[hook] Added tools: {[tool.name for tool in new_tools]}")
        # TODO: change the tool result! "Now you can use the tools {...}"

    async def on_agent_end(self, context: RunContextWrapper[UTUContext], agent: Agent[UTUContext], output: Any) -> None:
        """Cleanup MCP servers"""
        utu_context = context.context
        await utu_context.exit_stack.aclose()
        utu_context.dynamic_mcp_servers = []


class UTUToolMakerAgent(UTUSimpleAgent):
    def __init__(
        self,
        config_name: str = "tool_maker",
        name: str = None,
        instructions: str = None,
        *args, **kwargs
    ):
        super().__init__(config_name, name, instructions, *args, **kwargs)
        self.set_run_hooks(ToolMakerRunHooks())

    async def build(self):
        await super().build()
        self.context.current_agent.tools.append(make_tool)
