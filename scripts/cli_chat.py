import argparse
import asyncio

import art

from utu.agents import SimpleAgent, get_agent
from utu.config import AgentConfig, ConfigLoader
from utu.utils import PrintUtils, AgentsUtils

USAGE_MSG = f"""{"-" * 100}
Usage: `python cli_chat.py --config_name <config_name>`
Note: Multi-turn chat is only supported by SimpleAgent for now. We are working on this feature!
Quit: exit, quit, q
{"-" * 100}""".strip()


async def main():
    text = art.text2art("Youtu-agent", font="small")
    PrintUtils.print_info(text, color="blue")
    PrintUtils.print_info(USAGE_MSG, color="yellow")

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="simple/base", help="Configuration name")
    parser.add_argument("--agent_model", type=str, default=None, help="Agent model.")
    args = parser.parse_args()

    config: AgentConfig = ConfigLoader.load_agent_config(args.config_name)
    # Override basic configs
    if args.agent_model:
        assert config.type == "simple", f"--agent_model only support SimpleAgent, get {config.type}"
        config.model.model_provider.model = args.agent_model
    if config.type == "workforce":
        PrintUtils.print_info("Error: Workforce agent is not supported in CLI mode yet.")
        return

    agent = get_agent(config=config)
    while True:
        user_input = await PrintUtils.async_print_input("> ")
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            break
        if not user_input.strip():
            continue

        # if hasattr(agent, "build"):
        #     await agent.build()
        if isinstance(agent, SimpleAgent):
            async with agent:
                await agent.chat_streamed(user_input)
        else:
            res = agent.run_streamed(user_input)
            await AgentsUtils.print_stream_events(res.stream_events())


if __name__ == "__main__":
    asyncio.run(main())
