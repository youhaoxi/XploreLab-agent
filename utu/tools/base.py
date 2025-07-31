import abc
from typing import Callable

from agents import FunctionTool, function_tool
import mcp.types as types

from ..config import ToolkitConfig
from ..utils import ChatCompletionConverter


class MCPConverter:
    @classmethod
    def function_tool_to_mcp(cls, tool: FunctionTool) -> types.Tool:
        return types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.params_json_schema,
        )


class AsyncBaseToolkit(abc.ABC):
    config: ToolkitConfig
    tools_map: dict[str, Callable] = None
    
    def __init__(self, config: ToolkitConfig|dict|None = None):
        if not isinstance(config, ToolkitConfig):
            config = config or {}
            config = ToolkitConfig(config=config, name=self.__class__.__name__)
        self.config = config

    async def __aenter__(self):
        await self.build()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    async def build(self):
        pass

    async def cleanup(self):
        pass


    @abc.abstractmethod
    async def get_tools_map(self) -> dict[str, Callable]:
        pass

    async def get_tools_map_func(self) -> dict[str, Callable]:
        if self.tools_map is None:
            self.tools_map = await self.get_tools_map()
        if self.config.activated_tools:
            assert all(tool_name in self.tools_map for tool_name in self.config.activated_tools), f"Error config activated tools: {self.config.activated_tools}"
            tools_map = {tool_name: self.tools_map[tool_name] for tool_name in self.config.activated_tools}
        else:
            tools_map = self.tools_map
        return tools_map

    async def get_tools_in_agents(self) -> list[FunctionTool]:
        """ Convert tools to @agents format. """
        tools_map = await self.get_tools_map_func()
        tools = []
        for tool_name, tool in tools_map.items():
            tools.append(function_tool(
                tool, 
                strict_mode=False  # turn off strict mode
            ))
        return tools

    async def get_tools_in_openai(self) -> list[dict]:
        tools = await self.get_tools_in_agents()
        return [ChatCompletionConverter.tool_to_openai(tool) for tool in tools]
    
    async def get_tools_in_mcp(self) -> list[types.Tool]:
        tools = await self.get_tools_in_agents()
        return [MCPConverter.function_tool_to_mcp(tool) for tool in tools]

    async def call_tool(self, name: str, arguments: dict) -> str:
        tools_map = await self.get_tools_map_func()
        if name not in tools_map:
            raise ValueError(f"Tool {name} not found")
        tool = tools_map[name]
        return await tool(**arguments)
