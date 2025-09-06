import asyncio

from utu.agents import SimpleAgent
from utu.config import ConfigLoader

agent = SimpleAgent(config=ConfigLoader.load_agent_config("simple_agents/gaia_reasoning_coding.yaml"))


async def test_agent():
    await agent.build()
    print(f"agent with tools: {agent.tools}")
    await agent.chat_streamed("What tools do you have?")
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_agent())
