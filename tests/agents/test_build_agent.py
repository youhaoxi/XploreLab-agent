import pytest
import pandas as pd

from utu.agents import build_agent, UTUSimpleAgent


@pytest.fixture
async def agent() -> UTUSimpleAgent:
    agent: UTUSimpleAgent = build_agent("exp/v03")
    await agent.build()
    return agent

async def test_chat(agent: UTUSimpleAgent):
    async with agent:
        await agent.chat("Hello")

async def test_tools(agent: UTUSimpleAgent):
    openai_agent = agent.get_agent()
    tools = []
    for tool in openai_agent.tools:
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "schema": tool.params_json_schema,
        })
    df = pd.DataFrame(tools)
    df.to_csv("tools.csv", index=False)
    print(df)
