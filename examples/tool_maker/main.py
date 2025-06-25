import asyncio
from utu.agents import UTUToolMakerAgent


async def main():
    async with UTUToolMakerAgent(
        config_name="tool_maker",
        name="example-tool-maker-agent",
    ) as agent:
        await agent.chat("Make a tool to get the time, and tell me how to use it")


if __name__ == "__main__":
    asyncio.run(main())
