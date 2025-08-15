import asyncio
import json
import pathlib

from utu.agents import OrchestraAgent
from utu.config import ConfigLoader


async def main():
    config = ConfigLoader.load_agent_config("examples/paper_collector")
    config.planner_config["examples_path"] = pathlib.Path(__file__).parent / "planner_examples_data.json"
    runner = OrchestraAgent(config)
    await runner.build()

    # data from https://arxiv.org/abs/2507.12883
    fn = pathlib.Path(__file__).parent / "data" / "2507.12883v1-2.pdf"
    paper_url = "https://www.arxiv.org/pdf/2507.12883"
    question = f"请分析论文{paper_url}，整理出它的相关工作，并且进行简单的比较。"
    result = await runner.run(question)

    print(f"Run completed with result: {result}")
    with open(fn.parent / "result.json", "w", encoding="utf-8") as f:
        json.dump([task.model_dump() for task in result.task_records], f, ensure_ascii=False, indent=4)
    with open(fn.parent / "final_output.txt", "w", encoding="utf-8") as f:
        f.write(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
