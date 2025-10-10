import json

from agents import FunctionTool, RunContextWrapper, TContext, Tool

from ..utils import get_logger
from .base_env import Env
from .utils import MCPClient
from .utils.tione_manager import TioneEnvManager

logger = get_logger(__name__)


class BrowserTioneEnv(Env):
    def __init__(self):
        self.browser_state: str = None

    async def build(self):
        """Build the environment. We use docker to run a browser container."""
        tione_manager = TioneEnvManager(type="BROWSER_CHROMIUM")
        env_info = await tione_manager.create_env()
        self.mcp_url = f"http://{env_info['Endpoint']}/mcp/"

    def get_state(self) -> str:
        """Get the current state of the environment."""
        return self.browser_state

    async def get_tools(self) -> list[Tool]:
        """Get the tools available in the environment."""
        async with MCPClient.get_mcp_client(self.mcp_url) as client:

            def create_on_invoke_tool(tool_name: str):
                async def on_invoke_tool(ctx: RunContextWrapper[TContext], input_json: str) -> str:
                    try:
                        res = await client.call_tool(tool_name, json.loads(input_json))
                        if res.isError:
                            return f"Error: {res.content[0].text}"
                        self.browser_state = res.content[1].text  # DISCUSS: record the web actions?
                        return res.content[0].text
                    except Exception as e:
                        logger.error(f"except: {e}", exc_info=True)
                        return f"Error: {e}"

                return on_invoke_tool

            # NOTE: check `MCPUtil` in @agents
            res = await client.list_tools()
            assert res.nextCursor is None
            tools = []
            for tool in res.tools:
                tools.append(
                    FunctionTool(
                        name=tool.name,
                        description=tool.description,
                        params_json_schema=tool.inputSchema,
                        on_invoke_tool=create_on_invoke_tool(tool.name),
                    )
                )
            return tools
