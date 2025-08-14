from utu.config import ConfigLoader
from utu.ww.ww_agent import WWAgent

config = ConfigLoader.load_eval_config("ww")
agent = WWAgent(config.agent)


async def test_ww_agent():
    await agent.build()
    result = await agent.run("What is the capital of France?")
    print(result)
