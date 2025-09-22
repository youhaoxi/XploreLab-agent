"""Utils to inspect tools
- start a MCP server with all tools (can be checked with @modelcontextprotocol/inspector)
"""

import asyncio

from mcp.server.fastmcp import FastMCP
from mcp.types import AnyFunction

from utu.config import ConfigLoader
from utu.tools import (
    TOOLKIT_MAP,
    AsyncBaseToolkit,
)


def get_toolkits() -> dict[str, AsyncBaseToolkit]:
    toolkits = {}
    for name, toolkit in TOOLKIT_MAP.items():
        print(f"Loading toolkit: {name}")
        config = ConfigLoader.load_toolkit_config(name)
        toolkits[name] = toolkit(config=config)
    return toolkits


async def get_tools() -> dict[str, AnyFunction]:
    tools_fn = {}
    for _, toolkit in get_toolkits().items():
        tools_fn.update(await toolkit.get_tools_map())
    return tools_fn


def main():
    mcp = FastMCP(
        "Tools Test Server",
        host="0.0.0.0",
        port=3005,
    )
    tools_map = asyncio.run(get_tools())
    for name, tool in tools_map.items():
        mcp.add_tool(tool)
        print(f"Added tool: {name}")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
