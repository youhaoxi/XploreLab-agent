import json
from collections import defaultdict

from agents import RunResultStreaming, StopAtTools, trace

from ..agents import SimpleAgent
from ..tools import UserInteractionToolkit, get_toolkits_map
from ..utils import DIR_ROOT, AgentsUtils, get_jinja_env, get_logger

logger = get_logger(__name__)

TOOL_SELECTION_TEMPLATE = """<available_tools>
{available_tools}
</available_tools>
<requirement>
{requirement}
</requirement>"""

CONFIG_TEMPLATE = """
# @package _global_
defaults:
  - /model/base@model
{toolkits_includes}
  - _self_

toolkits:
{toolkits_configs}

agent:
  name: {agent_name}
  instructions: |
{instructions}
"""


def add_indented_lines(lines: str | list[str], indent: int = 2) -> str:
    if isinstance(lines, str):
        lines = lines.split("\n")
    return "\n".join(" " * indent + line for line in lines)


class SimpleAgentGenerator:
    def __init__(self):
        self.jinja_env = get_jinja_env(DIR_ROOT / "utu/prompts/meta")
        self.output_dir = DIR_ROOT / "configs/agents/generated"
        self.output_dir.mkdir(exist_ok=True)

        tools_list = UserInteractionToolkit().get_tools_in_agents_sync()
        self.agent_1 = SimpleAgent(
            name="clarification_agent",
            instructions=self.jinja_env.get_template("requirements_clarification.j2").render(),
            tools=tools_list,
            tool_use_behavior=StopAtTools(stop_at_tool_names=["final_answer"]),
        )
        self.agent_2 = SimpleAgent(
            name="tool_selection_agent",
            instructions=self.jinja_env.get_template("tools_selection.j2").render(),
        )
        self.agent_3 = SimpleAgent(
            name="instructions_generation_agent",
            instructions=self.jinja_env.get_template("instructions_generation.j2").render(),
        )
        self.agent_4 = SimpleAgent(
            name="name_generation_agent",
            instructions=self.jinja_env.get_template("name_generation.j2").render(),
        )

    async def run(self):
        with trace("simple_agent_generator"):
            user_input = input("> ")
            requirements = await self.step1(user_input)
            selected_tools = await self.step2(requirements)
            instructions = await self.step3(requirements)
            name = await self.step4(requirements)
            print(f"> requirements: {requirements}")
            print(f"> selected_tools: {selected_tools}")
            print(f"> instructions: {instructions}")
            print(f"> name: {name}")
        # format config
        toolkits_includes = []
        toolkits_configs = []
        for toolkit_name, tool_names in selected_tools.items():
            toolkits_includes.append(f"- /tools/{toolkit_name}@toolkits.{toolkit_name}")
            toolkits_configs.append(f"{toolkit_name}: {json.dumps({'activated_tools': tool_names})}")
        config = CONFIG_TEMPLATE.format(
            agent_name=name,
            instructions=add_indented_lines(instructions, 4),
            toolkits_includes=add_indented_lines(toolkits_includes, 2),
            toolkits_configs=add_indented_lines(toolkits_configs, 2),
        )
        (self.output_dir / f"{name}.yaml").write_text(config)
        print(f"Generated agent config saved to {self.output_dir / f'{name}.yaml'}!")

    async def step1(self, user_input: str) -> str:
        async with self.agent_1 as agent:
            result = agent.run_streamed(user_input)
            await self._process_streamed(result)
            return result.final_output

    async def step2(self, requirements: str) -> dict[str, list[str]]:
        """Select useful tools from available toolkits. Return: {toolkit_name: [tool_name, ...]}"""
        available_toolkits = ["search", "document", "image", "audio", "bash", "tabular"]
        toolkits_map = get_toolkits_map(names=available_toolkits)
        tools_descs = []
        tool_to_toolkit_name = {}
        for toolkit_name, toolkit in toolkits_map.items():
            tools = await toolkit.get_tools_in_agents()
            tools_descs.extend(f"- {tool.name}: {tool.description}" for tool in tools)
            tool_to_toolkit_name.update({tool.name: toolkit_name for tool in tools})
        tools_str = "\n".join(tools_descs)
        query = TOOL_SELECTION_TEMPLATE.format(
            available_tools=tools_str,
            requirement=requirements,
        )
        async with self.agent_2 as agent:
            result = agent.run_streamed(query)
            await self._process_streamed(result)
            selected_tools = result.final_output
            selected_tool_names = json.loads(selected_tools)
        selected_tools = defaultdict(list)
        for tool_name in selected_tool_names:
            selected_tools[tool_to_toolkit_name[tool_name]].append(tool_name)
        return selected_tools

    async def step3(self, requirements: str) -> str:
        """Generate instructions for the agent."""
        async with self.agent_3 as agent:
            result = agent.run_streamed(requirements)
            await self._process_streamed(result)
            instructions = result.final_output
        return instructions

    async def step4(self, requirements: str) -> str:
        """Generate instructions for the agent."""
        async with self.agent_4 as agent:
            result = agent.run_streamed(requirements)
            await self._process_streamed(result)
            name = result.final_output
            if len(name) > 50 or " " in name:
                logger.warning(f"Generated name is too long or contains spaces: {name}")
                name = name[:50].replace(" ", "_")
        return name

    async def _process_streamed(self, run_result_streaming: RunResultStreaming):
        await AgentsUtils.print_stream_events(run_result_streaming.stream_events())
