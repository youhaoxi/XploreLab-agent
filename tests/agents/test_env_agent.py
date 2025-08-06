import logging
import pytest

from utu.config import ConfigLoader
from utu.agents import SimpleEnvAgent


@pytest.fixture
async def agent():
    agent = SimpleEnvAgent(ConfigLoader.load_agent_config("web"))
    await agent.build()
    yield agent
    await agent.cleanup()

async def test_chat_streamed(agent: SimpleEnvAgent):
    tools = await agent.get_tools()
    logging.info(f"Loaded {len(tools)} tools: {tools}")
    
    await agent.chat_streamed("That's the weather in Beijing today?")
