""" 
Example evaluation script, with async rollout and concurrency control.
"""

import asyncio
import pathlib
import copy
import json
from agents.models.chatcmpl_converter import Converter

from utu.agents import SimpleAgent

flock = asyncio.Lock()
ofn = pathlib.Path(__file__).parent / "eval_result.jsonl"

data = [
    {"Topic": "体育", "Question": "在某个知名的葡萄酒产区中的某个地区存在一个只产某种葡萄酒的地区，距离此地区20-40公里范围内存在一家足球俱乐部，那么该足球俱乐部最近一次升入上一级联赛提前几轮确定？", "Answer": "1轮", "canary": "BrowseComp-ZH"},
    {"Topic": "影视", "Question": "20世纪二十年代中在上海成立的刊物成为了我国知名学生运动的先导，在此次运动中占据领导地位的高校在近百年后有一名在21世纪初某少儿电视剧中扮演重要角色的演员入学，那么请问在此电视剧中的男一号是什么时间结婚", "Answer": "2019年4月23日", "canary": "BrowseComp-ZH"}
]

async def rollout(agent: SimpleAgent, data: dict) -> dict:
    result = await agent.run(data["Question"])
    predicted = result.final_output

    output = copy.deepcopy(data)
    output["Answer Predicted"] = predicted
    output["trajectory"] = Converter.items_to_messages(result.to_input_list())
    async with flock:
        with open(ofn, "a") as f:
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")
    return output

async def main(concurrency: int = 5):
    async with SimpleAgent(
        "examples/eval",
        name="example-eval-agent",
        instructions="You should answer the question with the tools provided."
    ) as agent:
        semaphore = asyncio.Semaphore(concurrency)

        async def rollout_with_semaphore(agent, item):
            async with semaphore:
                return await rollout(agent, item)

        print(f"Rolling out {len(data)} items with {concurrency} concurrency...")
        tasks = [rollout_with_semaphore(agent, item) for item in data]
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            print(f" {i+1:03d}/{len(data)} ".center(50, "-"))
            print(f"Question: {result['Question']}")
            print(f"Answer: {result['Answer']}")
            print(f"Result: {result['Answer Predicted']}")

if __name__ == "__main__":
    asyncio.run(main(concurrency=5))
