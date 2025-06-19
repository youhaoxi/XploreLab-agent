import asyncio
from agents import Agent
from utu.agents.base import UTUAgentBase
from utu.utils import AgentsUtils, get_package_path
from utu.config import load_config

sample_data = [
    {"Topic": "体育", "Question": "在某个知名的葡萄酒产区中的某个地区存在一个只产某种葡萄酒的地区，距离此地区20-40公里范围内存在一家足球俱乐部，那么该足球俱乐部最近一次升入上一级联赛提前几轮确定？", "Answer": "1轮", "canary": "BrowseComp-ZH"},
    {"Topic": "影视", "Question": "20世纪二十年代中在上海成立的刊物成为了我国知名学生运动的先导，在此次运动中占据领导地位的高校在近百年后有一名在21世纪初某少儿电视剧中扮演重要角色的演员入学，那么请问在此电视剧中的男一号是什么时间结婚", "Answer": "2019年4月23日", "canary": "BrowseComp-ZH"}
]

def build_agent():
    agent = UTUAgentBase()
    config = load_config(get_package_path() / "configs" / "default.yaml")
    model = AgentsUtils.get_agents_model(config.model.model, config.model.api_key, config.model.base_url)
    current_agent = Agent(
        name="eval-agent",
        instructions="You are a helpful assistant.",
        model=model,
    )
    agent.set_agent(current_agent)
    return agent

def load_data():
    return sample_data

async def main():
    agent = build_agent()
    data = load_data()
    for i, item in enumerate(data):
        result = await agent.run(item["Question"])
        print(f"{i+1: 03d}. Question: {item['Question']}")
        print(f"Answer: {item['Answer']}")
        print(f"Result: {result.final_output}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
