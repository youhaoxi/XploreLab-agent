import json

import pytest

from utu.agents import SimpleAgent
from utu.config import ConfigLoader


@pytest.fixture
async def agent():
    agent = SimpleAgent(config=ConfigLoader.load_agent_config("default"))
    await agent.build()
    yield agent
    await agent.cleanup()


async def test_chat_streamed(agent: SimpleAgent):
    run_result_streaming = await agent.chat_streamed("That's the weather in Beijing today?")
    print(run_result_streaming)


async def test_chat(agent: SimpleAgent):
    run_result = await agent.chat("That's the weather in Beijing today?")
    print(json.dumps(run_result.to_input_list(), ensure_ascii=False, indent=2))
