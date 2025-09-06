# noqa: E501

import asyncio

from utu.agents import SimpleAgent
from utu.config import ConfigLoader


async def test_reasoning_coding_agent():
    agent = SimpleAgent(config=ConfigLoader.load_agent_config("simple_agents/gaia_reasoning_coding.yaml"))
    await agent.build()
    print(f"agent with tools: {agent.tools}")
    # await agent.chat_streamed("What tools do you have?")
    # await agent.chat_streamed("analysis data/gaia/2023/validation/3da89939-209c-4086-8520-7eb734e6b4ef.xlsx")
    await agent.chat_streamed("analysis data/gaia/2023/validation/9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip")
    await agent.cleanup()


async def test_web_search_agent():
    agent = SimpleAgent(config=ConfigLoader.load_agent_config("simple_agents/gaia_web_search.yaml"))
    await agent.build()
    print(f"agent with tools: {agent.tools}")
    await agent.chat_streamed("What tools do you have?")
    await agent.chat_streamed(
        "How many studio albums were published by Mercedes Sosa between 2000 and 2009 (included)?"
    )
    await agent.cleanup()


async def test_main():
    # await test_reasoning_coding_agent()
    await test_web_search_agent()


if __name__ == "__main__":
    asyncio.run(test_main())
