# pylint: disable=line-too-long
# ruff: noqa: E501
"""
https://manus.im/blog/introducing-wide-research
"""

import asyncio
import json
import pathlib
import traceback

from agents import AgentOutputSchema, function_tool

from utu.agents import SimpleAgent
from utu.config import ConfigLoader
from utu.tools import SearchToolkit
from utu.ui.webui_chatbot import WebUIChatbot
from utu.utils import FileUtils, schema_to_basemodel

PROMPTS = FileUtils.load_yaml(pathlib.Path(__file__).parent / "prompts.yaml")
SEARCH_TOOLKIT = SearchToolkit(ConfigLoader.load_toolkit_config("search"))
CONCURRENCY = 20


@function_tool(strict_mode=False)
async def wide_research(task: str, subtasks: list[str], output_schema: dict, output_fn: str) -> str:
    """Perform wide research. Given subtasks of the root task, this tool will perform subtasks simultaneously, saving to a jsonl file.

    NOTEs:
    - Only call this tool when you are sure that 1) it has >= 5 subtasks; 2) the subtasks are homogeneous that can be completed by the same procedure.

    Args:
        task (str): The root task to perform research on.
        subtasks (list[str]): Subtasks contained in the root task. They should be homogeneous that can be completed by the same procedure.
        output_schema (dict): The desired output format of each subtask, MUST be valid JSON Schema. e.g.
          {"properties": {"provider": {"description": "The model provider", "title": "Provider", "type": "string"}, "model_name": {"description": "The model name", "title": "Model Name", "type": "string"}, "context_window": {"description": "The context window", "type": "integer"}, "required": ["provider", "model_name", "context_window"], "title": "LLM", "type": "object"}
        output_fn (str): The file name to save the output, in JSONL format. e.g. `output.jsonl`
    """
    # print(f"task: {task}\nsubtasks: {subtasks}\noutput_schema: {output_schema}")
    output_type = schema_to_basemodel(output_schema)
    print(f"Processing {len(subtasks)} subtasks for task: {task}\nOutput schema: {output_schema}")
    try:
        searcher = SimpleAgent(
            name="SearcherAgent",
            instructions=PROMPTS["searcher"],
            tools=await SEARCH_TOOLKIT.get_tools_in_agents(),
            output_type=AgentOutputSchema(output_type=output_type, strict_json_schema=False),
        )
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def run_with_semaphore(idx: int, task: str) -> str:
            async with semaphore:
                try:
                    async with searcher:
                        res = await searcher.run(task)
                        final_output = res.get_run_result().final_output
                    print(f"{idx}: `{task}` task finished!")
                    return final_output.model_dump()
                except Exception as e:
                    print(f"Error: {e}")
                    traceback.print_exc()
                    return f"Error: {e}"

        results = await asyncio.gather(*[run_with_semaphore(i, subtask) for i, subtask in enumerate(subtasks)])
        output_fn = pathlib.Path(__file__).parent / output_fn
        with open(output_fn, "w") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        with open(output_fn) as f:
            return f"Results saved to {output_fn}:\n" + f.read()
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"


TASK = "Find the outstanding papers of ACL 2025, extract their title, author list, keywords, abstract, url in one sentence."


class WideResearch:
    async def build(self):
        self.planner_agent = SimpleAgent(
            name="PlannerAgent",
            instructions=PROMPTS["planner"],
            tools=[wide_research] + await SEARCH_TOOLKIT.get_tools_in_agents(),
        )

    async def run(self, task: str):
        async with self.planner_agent as planner:
            result = await planner.run(task)
            output = result.get_run_result().final_output
            return output

    async def run_webui(self):
        chatbot = WebUIChatbot(
            self.planner_agent,
            example_query=TASK,
        )
        await chatbot.launch_async()


async def main():
    wide_research = WideResearch()
    await wide_research.build()
    await wide_research.run_webui()


if __name__ == "__main__":
    asyncio.run(main())
