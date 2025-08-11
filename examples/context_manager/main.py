import asyncio
from agents import function_tool

from utu.agents import SimpleAgent
from utu.config import ConfigLoader


COUNT = 0
@function_tool
def count() -> int:
    global COUNT
    COUNT += 1
    return COUNT


queries = [
    "Use the count tool for 20 times, and give me the sum of the results. Note that you can only use one tool per turn.",
]

async def main():
    config = ConfigLoader.load_agent_config("examples/base")
    config.max_turns = 100
    async with SimpleAgent(
        config=config,
        name="example-context-manager",
        tools=[count],
    ) as agent:
        for query in queries:
            await agent.chat_streamed(query)


if __name__ == "__main__":
    asyncio.run(main())
