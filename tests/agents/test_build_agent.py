from utu.agents import build_agent, UTUSimpleAgent

async def test_build_agent():
    agent: UTUSimpleAgent = build_agent("v01")
    async with agent:
        await agent.chat("Hello")
