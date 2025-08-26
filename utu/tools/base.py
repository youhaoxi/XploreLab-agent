import abc
from collections.abc import Callable

import mcp.types as types
from agents import FunctionTool, function_tool

from ..config import ToolkitConfig
from ..utils import DIR_ROOT, ChatCompletionConverter, FileUtils, get_event_loop


class MCPConverter:
    @classmethod
    def function_tool_to_mcp(cls, tool: FunctionTool) -> types.Tool:
        return types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.params_json_schema,
        )


class AsyncBaseToolkit(abc.ABC):
    """Base class for toolkits."""

    config: ToolkitConfig
    tools_map: dict[str, Callable] = None

    def __init__(self, config: ToolkitConfig | dict | None = None):
        if not isinstance(config, ToolkitConfig):
            config = config or {}
            config = ToolkitConfig(config=config, name=self.__class__.__name__)
        self.config = config
        self._built = False

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def build(self):
        if self._built:
            return
        self._built = True

    async def cleanup(self):
        self._built = False

    @abc.abstractmethod
    async def get_tools_map(self) -> dict[str, Callable]:
        """Abstract method to get tools map.

        Returns:
            dict[str, Callable]: A dictionary of tool names to their corresponding functions.
        """
        pass

    async def get_tools_map_func(self) -> dict[str, Callable]:
        """Get tools map. It will filter tools by config.activated_tools if it is not None."""
        if self.tools_map is None:
            self.tools_map = await self.get_tools_map()
        if self.config.activated_tools:
            assert all(tool_name in self.tools_map for tool_name in self.config.activated_tools), (
                f"Error config activated tools: {self.config.activated_tools}! available tools: {self.tools_map.keys()}"
            )
            tools_map = {tool_name: self.tools_map[tool_name] for tool_name in self.config.activated_tools}
        else:
            tools_map = self.tools_map
        return tools_map

    async def get_tools_in_agents(self) -> list[FunctionTool]:
        """Get tools in openai-agents format."""
        tools_map = await self.get_tools_map_func()
        tools = []
        for _, tool in tools_map.items():
            tools.append(
                function_tool(
                    tool,
                    strict_mode=False,  # turn off strict mode
                )
            )
        return tools

    async def get_tools_in_openai(self) -> list[dict]:
        """Get tools in OpenAI format."""
        tools = await self.get_tools_in_agents()
        return [ChatCompletionConverter.tool_to_openai(tool) for tool in tools]

    async def get_tools_in_mcp(self) -> list[types.Tool]:
        """Get tools in MCP format."""
        tools = await self.get_tools_in_agents()
        return [MCPConverter.function_tool_to_mcp(tool) for tool in tools]

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool by its name."""
        tools_map = await self.get_tools_map_func()
        if name not in tools_map:
            raise ValueError(f"Tool {name} not found")
        tool = tools_map[name]
        return await tool(**arguments)

    # -------------------------------------------------------------------------------------------------------------
    def get_tools_map_sync(self) -> dict[str, Callable]:
        if self.tools_map is None:
            loop = get_event_loop()
            if not self._built:
                loop.run_until_complete(self.build())
            self.tools_map = loop.run_until_complete(self.get_tools_map_func())
        return self.tools_map

    def get_tools_in_agents_sync(self) -> list[FunctionTool]:
        tools_map = self.get_tools_map_sync()
        tools = []
        for _, tool in tools_map.items():
            tools.append(
                function_tool(
                    tool,
                    strict_mode=False,  # turn off strict mode
                )
            )
        return tools


TOOL_PROMPTS: dict[str, str] = FileUtils.load_yaml(DIR_ROOT / "utu" / "prompts" / "tools" / "tools_prompts.yaml")
