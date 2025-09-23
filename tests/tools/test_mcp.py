from agents.mcp import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp

from utu.config import ConfigLoader, ToolkitConfig


def get_mcp_server(config: ToolkitConfig):
    assert config.mode == "mcp", f"config mode must be 'mcp', got {config.mode}"
    match config.mcp_transport:
        case "stdio":
            return MCPServerStdio(
                params=config.config,
                name=config.name,
                client_session_timeout_seconds=config.mcp_client_session_timeout_seconds,
            )
        case "sse":
            return MCPServerSse(
                params=config.config,
                name=config.name,
                client_session_timeout_seconds=config.mcp_client_session_timeout_seconds,
            )
        case "streamable_http":
            return MCPServerStreamableHttp(
                params=config.config,
                name=config.name,
                client_session_timeout_seconds=config.mcp_client_session_timeout_seconds,
            )
        case _:
            raise ValueError(f"Unsupported mcp transport: {config.mcp_transport}")


async def test_mcp():
    # config_name = "mcp/time"
    # action = [("get_current_time", {"timezone": "Asia/Shanghai"})]
    # config_name = "mcp/sequentialthinking"
    # action = [("sequentialthinking", {"thought": "step 1", "nextThoughtNeeded": False, "thoughtNumber": 1, "totalThoughts": 1})]

    # config_name = "mcp/context7"
    # action = [("get-library-docs", {"context7CompatibleLibraryID": "/mongodb/docs"})]
    config_name = "mcp/github"
    action = [("search_repositories", {"query": "youtu-agent"})]

    # config_name = "mcp/mem0"
    # action = [("add_memories", {"text": "I like to eat bagels"}), ("list_memories", {})]

    config = ConfigLoader.load_toolkit_config(config_name)
    mcp_server = get_mcp_server(config)
    async with mcp_server:
        tools = await mcp_server.list_tools()
        print("Tools:", tools)
        for name, params in action:
            print(f"Calling tool: {name} with params: {params}")
            res = await mcp_server.call_tool(name, params)
            print(f"> res: {res}")
