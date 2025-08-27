import asyncio
import pathlib

from utu.agents import OrchestraAgent
from utu.config import ConfigLoader


async def main():
    config = ConfigLoader.load_agent_config("examples/svg_generator")
    config.planner_config["examples_path"] = pathlib.Path(__file__).parent / "planner_examples.json"
    config.reporter_config["template_path"] = pathlib.Path(__file__).parent / "reporter_csv.j2"
    runner = OrchestraAgent(config)
    await runner.build()

    data_dir = pathlib.Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    question = "deepseek-v3.1有哪些亮点更新?"

    result = runner.run_streamed(question)
    async for event in result.stream_events():
        print(event)
    # print(result)
    # print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
