import pathlib
import asyncio
import contextlib

from agents import Agent
from agents.mcp import MCPServerStdio, MCPServer

from utu.agents.base import UTUAgentBase
from utu.utils import AgentsUtils, DIR_ROOT
from utu.config import load_config


class MCPAgent(UTUAgentBase):
    def __init__(self, mcp_servers: list[MCPServer]) -> None:
        config = load_config(DIR_ROOT / "configs" / "default.yaml")
        model = AgentsUtils.get_agents_model(config.model.model, config.model.api_key, config.model.base_url)
        agent = Agent(
            name="mcp-agent",
            instructions="You are a helpful assistant.",
            model=model,
            mcp_servers=mcp_servers,
        )
        self._current_agent = agent

def build_agent(mcp_servers: list[MCPServer]) -> MCPAgent:
    agent = MCPAgent(mcp_servers)
    return agent


mcp_servers_config = {
    "time": {
        "command": "uvx",
        "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"]
    },
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "env": {
            "MEMORY_FILE_PATH": str(pathlib.Path(__file__).parent / "memory.jsonl")
        }
    }
}
# from https://en.wikipedia.org/wiki/Anthropic
doc = """Anthropic PBC is an American artificial intelligence (AI) startup company founded in 2021. Anthropic has developed a family of large language models (LLMs) named Claude as a competitor to OpenAI's ChatGPT and Google's Gemini.[5] According to the company, it researches and develops AI to "study their safety properties at the technological frontier" and use this research to deploy safe models for the public.[6][7]
Anthropic was founded by former members of OpenAI, including siblings Daniela Amodei and Dario Amodei.[8] In September 2023, Amazon announced an investment of up to $4 billion, followed by a $2 billion commitment from Google in the following month.[9][10][11]"""
queries = [
    "What is the time now?",
    # f"Add memory: {doc}",
    # "Who are the founders of Anthropic?",
]

async def main():
    with contextlib.suppress(asyncio.CancelledError):
        try:
            # start the mcp servers
            print("> Starting MCP servers...")
            servers: list[MCPServer] = []
            for name, params in mcp_servers_config.items():
                server = MCPServerStdio(
                    name=name, 
                    params=params,
                    client_session_timeout_seconds=20,
                )
                await server.connect()
                servers.append(server)
            
            # build the agent & chat
            print("> Building agent...")
            agent = build_agent(servers)
            for query in queries:
                await agent.chat(query)
            print("> Done")
        except Exception as e:
            print(f"Failed with exception {type(e)}: {e}")
        finally:
            # close the servers
            for server in servers:
                await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
