# pylint: disable=line-too-long
# ruff: noqa: E501

import asyncio

from agents import function_tool

from utu.agents import SimpleAgent
from utu.config import ConfigLoader
from utu.tools import SearchToolkit


def get_tools():
    toolkit = SearchToolkit(ConfigLoader.load_toolkit_config("search"))
    return toolkit.get_tools_in_agents_sync()


search_tools = get_tools()


@function_tool(strict_mode=False)
def wide_research(task: str, subtasks: list[str], output_schema: dict) -> str:
    """Perform wide research on a given task. Given a task with several subtasks, this tool will complete the subtasks simultaneously.

    Args:
        task (str): The root task to perform research on.
        subtasks (list[str]): Subtasks contained in the root task. They should be homogeneous that can be completed by the same procedure.
        output_schema (dict): The desired output format of each subtask, MUST be valid JSON Schema.
    """
    print(f"task: {task}\nsubtasks: {subtasks}\noutput_schema: {output_schema}")


SP = """You are a helpful research assistant.
- If the task contains homogeneous subtasks that can be handled in parallel, use the wide_research tool.
- After gathering enough information, response to the user directly.
"""


def build_planner():
    return SimpleAgent(
        name="PlannerAgent",
        instructions=SP,
        tools=[wide_research] + search_tools,
    )


TASK = (
    "Find the outstanding papers of ACL 2025, extract their title, author list, keywords, and abstract in one sentence."
)


async def main():
    async with build_planner() as agent:
        result = await agent.run(TASK)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
