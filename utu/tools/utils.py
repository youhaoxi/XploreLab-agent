import re
from collections.abc import Callable

from agents import Agent, RunContextWrapper
from agents.function_schema import FuncSchema, function_schema
from agents.mcp import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp, ToolFilterStatic
from mcp import Tool as MCPTool

from ..config import ToolkitConfig

MCP_SERVER_MAP = {
    "sse": MCPServerSse,
    "stdio": MCPServerStdio,
    "streamable_http": MCPServerStreamableHttp,
}


def get_mcp_server(config: ToolkitConfig) -> MCPServerSse | MCPServerStdio | MCPServerStreamableHttp:
    """Get mcp server from config, with tool_filter if activated_tools is set.
    NOTE: you should manage the lifecycle of the returned server (.connect & .cleanup), e.g. using `async with`."""
    assert config.mode == "mcp", f"config mode must be 'mcp', got {config.mode}"
    assert config.mcp_transport in MCP_SERVER_MAP, f"Unsupported mcp transport: {config.mcp_transport}"
    tool_filter = ToolFilterStatic(allowed_tool_names=config.activated_tools) if config.activated_tools else None
    return MCP_SERVER_MAP[config.mcp_transport](
        params=config.config,
        name=config.name,
        client_session_timeout_seconds=config.mcp_client_session_timeout_seconds,
        tool_filter=tool_filter,
    )


async def get_mcp_tools(config: ToolkitConfig) -> list[MCPTool]:
    async with get_mcp_server(config) as mcp_server:
        # It is required to pass agent and run_context when using `tool_filter`, we pass a dummy agent here
        tools = await mcp_server.list_tools(agent=Agent(name="dummy"), run_context=RunContextWrapper(context=None))
        return tools


async def get_mcp_tools_schema(config: ToolkitConfig) -> dict[str, FuncSchema]:
    tools = await get_mcp_tools(config)
    tools_map = {}
    for tool in tools:
        tools_map[tool.name] = FuncSchema(
            name=tool.name,
            description=tool.description,
            params_pydantic_model=None,
            params_json_schema=tool.inputSchema,
            signature=None,
        )
    return tools_map


class ContentFilter:
    def __init__(self, banned_sites: list[str] = None):
        if banned_sites:
            self.RE_MATCHED_SITES = re.compile(r"^(" + "|".join(banned_sites) + r")")
        else:
            self.RE_MATCHED_SITES = None

    def filter_results(self, results: list[dict], limit: int, key: str = "link") -> list[dict]:
        # can also use search operator `-site:huggingface.co`
        # ret: {title, link, snippet, position, | sitelinks}
        res = []
        for result in results:
            if self.RE_MATCHED_SITES is None or not self.RE_MATCHED_SITES.match(result[key]):
                res.append(result)
            if len(res) >= limit:
                break
        return res


def get_tools_map(cls: type) -> dict[str, Callable]:
    """Get tools map from a class, without instance the class."""
    tools_map = {}
    # Iterate through all methods of the class and register @tool
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and getattr(attr, "_is_tool", False):
            tools_map[attr._tool_name] = attr
    return tools_map


def get_tools_schema(cls: type) -> dict[str, FuncSchema]:
    """Get tools schema from a class, without instance the class."""
    tools_map = {}
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and getattr(attr, "_is_tool", False):
            tools_map[attr._tool_name] = function_schema(attr)
    return tools_map
