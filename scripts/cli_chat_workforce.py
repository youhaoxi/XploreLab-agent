import argparse
import asyncio

import art

from utu.agents import get_agent
from utu.config import AgentConfig, ConfigLoader
from utu.utils import PrintUtils

USAGE_MSG = f"""{"-" * 100}
Usage: python cli_chat.py --config_name <config_name>
Quit: exit, quit, q
{"-" * 100}""".strip()


async def main():
    text = art.text2art("Youtu-agent", font="small")
    PrintUtils.print_info(text, color="blue")
    PrintUtils.print_info(USAGE_MSG, color="yellow")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="workforce/base", help="Configuration name")
    parser.add_argument("--stream", action="store_true", help="Stream the output.")
    args = parser.parse_args()

    config: AgentConfig = ConfigLoader.load_agent_config(args.config_name)

    agent = get_agent(config=config)
    while True:
        user_input = await PrintUtils.async_print_input("> ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        if args.stream:
            await agent.run_streamed(user_input)
        else:
            await agent.run(user_input)


if __name__ == "__main__":
    asyncio.run(main())
