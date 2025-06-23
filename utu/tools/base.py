import abc
from typing import Callable

from agents import FunctionTool, function_tool
from agents.models.chatcmpl_converter import Converter
import mcp.types as types


class MCPConverter:
    @classmethod
    def function_tool_to_mcp(cls, tool: FunctionTool) -> types.Tool:
        return types.Tool(
            name=tool.name,
            description=tool.description,
            inputSchema=tool.params_json_schema,
        )


class AsyncBaseToolkit(abc.ABC):
    @abc.abstractmethod
    async def get_tools_map(self) -> dict[str, Callable]:
        pass

    async def get_tools_in_agents(self) -> list[FunctionTool]:
        """ Convert tools to @agents format. """
        tools_map = await self.get_tools_map()
        tools = []
        for tool_name, tool in tools_map.items():
            tools.append(function_tool(tool))
        return tools

    async def get_tools_in_openai(self) -> list[dict]:
        tools = await self.get_tools_in_agents()
        return [Converter.tool_to_openai(tool) for tool in tools]
    
    async def get_tools_in_mcp(self) -> list[types.Tool]:
        tools = await self.get_tools_in_agents()
        return [MCPConverter.function_tool_to_mcp(tool) for tool in tools]

    async def call_tool(self, name: str, arguments: dict) -> str:
        tools_map = await self.get_tools_map()
        if name not in tools_map:
            raise ValueError(f"Tool {name} not found")
        tool = tools_map[name]
        return await tool(**arguments)
