import argparse
import asyncio

from utu.config import ConfigLoader, AgentConfig
from utu.agents import SimpleAgent

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="default", help="Configuration name")
    parser.add_argument("--agent_model", type=str, default=None, help="Agent model.")
    parser.add_argument("--tools", type=str, nargs="*", help="List of tool names to load")
    args = parser.parse_args()

    config: AgentConfig = ConfigLoader.load_agent_config(args.config_name)
    if args.agent_model:
        config.model.model = args.agent_model
    if args.tools:
        # load toolkits from config
        for tool_name in args.tools:
            config.toolkits[tool_name] = ConfigLoader.load_toolkit_config(tool_name)

    async with SimpleAgent(config) as agent:
        while True:
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break
            await agent.chat(user_input)

if __name__ == "__main__":
    asyncio.run(main())
