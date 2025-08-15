import asyncio
import json
import pathlib

from utu.agents import OrchestraAgent
from utu.config import ConfigLoader


async def main():
    config = ConfigLoader.load_agent_config("examples/data_analysis")
    config.planner_config["examples_path"] = pathlib.Path(__file__).parent / "planner_examples_data.json"
    runner = OrchestraAgent(config)
    await runner.build()

    # data from https://www.kaggle.com/datasets/joannanplkrk/its-raining-cats
    fn = pathlib.Path(__file__).parent / "data" / "cat_breeds_clean.csv"
    question = f"请分析位于`{fn}`的猫品种数据，提取有价值的信息。"
    result = await runner.run(question)

    print(f"Run completed with result: {result}")
    with open(fn.parent / "result.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
