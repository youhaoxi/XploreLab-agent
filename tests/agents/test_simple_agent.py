import pytest

from utu.config import ConfigLoader
from utu.agents import SimpleAgent


@pytest.fixture
async def agent():
    agent = SimpleAgent(ConfigLoader.load_agent_config("default"))
    await agent.build()
    yield agent
    await agent.cleanup()

async def test_chat_streamed(agent: SimpleAgent):
    await agent.chat_streamed("That's the weather in Beijing today?")
