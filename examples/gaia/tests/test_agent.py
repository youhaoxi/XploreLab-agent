import asyncio

from utu.agents import SimpleAgent
from utu.config import ConfigLoader

agent = SimpleAgent(config=ConfigLoader.load_agent_config("simple_agents/gaia_reasoning_coding.yaml"))


async def test_agent():
    await agent.build()
    print(f"agent with tools: {agent.tools}")
    # await agent.chat_streamed("What tools do you have?")
    # await agent.chat_streamed("analysis data/gaia/2023/validation/3da89939-209c-4086-8520-7eb734e6b4ef.xlsx")
    await agent.chat_streamed("analysis data/gaia/2023/validation/9b54f9d9-35ee-4a14-b62f-d130ea00317f.zip")
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_agent())
