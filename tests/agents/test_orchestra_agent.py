import json

import pytest

from utu.agents import OrchestraAgent
from utu.config import ConfigLoader


@pytest.fixture
async def agent():
    agent = OrchestraAgent(config=ConfigLoader.load_agent_config("orchestra"))
    await agent.build()
    yield agent


async def test_run(agent: OrchestraAgent):
    run_result = await agent.run("Introduce the main architectures of CNN")
    print(json.dumps(run_result.to_dict(), ensure_ascii=False, indent=2))


async def test_run_streamed(agent: OrchestraAgent):
    run_result = agent.run_streamed("Introduce the main architectures of CNN")
    async for event in run_result.stream_events():
        print(event)


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = OrchestraAgent(config=ConfigLoader.load_agent_config("orchestra"))
        await agent.build()
        await test_run_streamed(agent)

    asyncio.run(main())
