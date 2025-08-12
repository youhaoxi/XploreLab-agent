import json

import pytest

from utu.config import ConfigLoader
from utu.agents import OrchestraAgent


@pytest.fixture
async def agent():
    agent = OrchestraAgent(config=ConfigLoader.load_agent_config("orchestra"))
    await agent.build()
    yield agent

async def test_chat(agent: OrchestraAgent):
    run_result = await agent.run("Introduce the main architectures of CNN")
    print(json.dumps(run_result.model_dump(), ensure_ascii=False, indent=2))
