import pathlib

from utu.agents import OrchestraAgent
from utu.config import ConfigLoader
from utu.ui.webui_chatbot import WebUIChatbot


def main():
    config = ConfigLoader.load_agent_config("examples/paper_collector")
    config.planner_config["examples_path"] = pathlib.Path(__file__).parent / "planner_examples_data.json"
    runner = OrchestraAgent(config)

    data_dir = pathlib.Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    paper_url = "https://www.arxiv.org/pdf/2507.12883"
    question = f"请分析论文{paper_url}，整理出它的相关工作，并且进行简单的比较。"

    ui = WebUIChatbot(runner, example_query=question)
    ui.launch()


if __name__ == "__main__":
    main()
