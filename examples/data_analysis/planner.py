import json
import pathlib
import re

from utu.agents.orchestra.common import AgentInfo, CreatePlanResult, OrchestraTaskRecorder, Subtask
from utu.config import AgentConfig
from utu.tools import TabularDataToolkit
from utu.utils import SimplifiedAsyncOpenAI, get_jinja_env


class OutputParser:
    def __init__(self):
        self.analysis_pattern = r"<analysis>(.*?)</analysis>"
        self.plan_pattern = r"<plan>\s*\[(.*?)\]\s*</plan>"
        # self.next_step_pattern = r'<next_step>\s*<agent>\s*(.*?)\s*</agent>\s*<task>\s*(.*?)\s*</task>\s*</next_step>'
        # self.task_finished_pattern = r'<task_finished>\s*</task_finished>'

    def parse(self, output_text: str) -> CreatePlanResult:
        analysis = self._extract_analysis(output_text)
        plan = self._extract_plan(output_text)
        return CreatePlanResult(analysis=analysis, todo=plan)

    def _extract_analysis(self, text: str) -> str:
        match = re.search(self.analysis_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_plan(self, text: str) -> list[Subtask]:
        match = re.search(self.plan_pattern, text, re.DOTALL)
        if not match:
            return []
        plan_content = match.group(1).strip()
        tasks = []
        task_pattern = r'\{"agent_name":\s*"([^"]+)",\s*"task":\s*"([^"]+)",\s*"completed":\s*(true|false)\s*\}'
        task_matches = re.findall(task_pattern, plan_content, re.IGNORECASE)
        for agent_name, task_desc, completed_str in task_matches:
            completed = completed_str.lower() == "true"
            tasks.append(Subtask(agent_name=agent_name, task=task_desc, completed=completed))
        return tasks


class PlannerAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = SimplifiedAsyncOpenAI(**self.config.planner_model.model_provider.model_dump())
        self.output_parser = OutputParser()
        self.jinja_env = get_jinja_env(
            pathlib.Path(__file__).parent.parent.parent / "utu" / "agents" / "orchestra" / "prompts"
        )
        self.planner_examples = self._load_planner_examples()
        self.available_agents = self._load_available_agents()

    def _load_planner_examples(self) -> list[dict]:
        examples_path = self.config.planner_config.get("examples_path", "")
        if examples_path and pathlib.Path(examples_path).exists():
            examples_path = pathlib.Path(examples_path)
        else:
            examples_path = pathlib.Path(__file__).parent / "data" / "planner_examples.json"
        with open(examples_path, encoding="utf-8") as f:
            return json.load(f)

    def _load_available_agents(self) -> list[AgentInfo]:
        available_agents = []
        for info in self.config.workers_info:
            available_agents.append(AgentInfo(**info))
        return available_agents

    async def build(self):
        pass

    async def create_plan(self, task_recorder: OrchestraTaskRecorder) -> CreatePlanResult:
        background_info = await self._get_background_info(task_recorder)
        sp = self.jinja_env.get_template("planner_sp.j2").render(
            planning_examples=self._format_planner_examples(self.planner_examples)
        )
        up = self.jinja_env.get_template("planner_up.j2").render(
            available_agents=self._format_available_agents(self.available_agents),
            question=task_recorder.task,
            background_info=background_info,  # TODO: add background info?
        )
        messages = [{"role": "system", "content": sp}, {"role": "user", "content": up}]
        response = await self.llm.query_one(messages=messages, **self.config.planner_model.model_params.model_dump())
        return self.output_parser.parse(response)

    async def update_plan(
        self, task_recorder: OrchestraTaskRecorder, current_step: int, add_background: bool = False
    ) -> CreatePlanResult:
        if add_background:
            background_info = self._get_background_info(task_recorder)
        else:
            background_info = ""
        sp = self.jinja_env.get_template("planner_update_sp.j2").render(
            planning_examples=self._format_planner_examples(self.planner_examples)
        )
        up = self.jinja_env.get_template("planner_update_up.j2").render(
            available_agents=self._format_available_agents(self.available_agents),
            question=task_recorder.task,
            background_info=background_info,
            previous_plan=task_recorder.get_plan_str(),
            task=task_recorder.plan.todo[current_step - 1].task if current_step > 0 else "",
            task_result=task_recorder.task_records[-1].output if task_recorder.task_records else "",
        )
        messages = [{"role": "system", "content": sp}, {"role": "user", "content": up}]
        response = await self.llm.query_one(messages=messages, **self.config.planner_model.model_params.model_dump())
        return self.output_parser.parse(response)

    async def _get_background_info(self, task_recorder: OrchestraTaskRecorder) -> str:
        """Get tabular column information for the task recorder."""
        data_analysis_tool = TabularDataToolkit()
        file_path = self._extract_file_path(task_recorder.task)
        if not file_path:
            return ""
        columns_info = await data_analysis_tool.get_column_info(file_path)
        info_str = f"Data columns of `{file_path}`:\n{columns_info}" if columns_info else ""
        info_str += ("\n**Note**: These background information is invisible to other agents, "
                     "but can help you to make better plan. So your plan should be based on the assumption "
                      "that the agents is initially unaware of this information.")
        return info_str

    def _extract_file_path(self, task: str) -> str:
        """Extract file path from the task description."""
        match = re.search(r"`([^`]+)`", task)
        if match:
            return match.group(1).strip()
        return ""

    def _format_planner_examples(self, examples: list[dict]) -> str:
        # format examples to string. example: {question, available_agents, analysis, plan}
        examples_str = []
        for example in examples:
            examples_str.append(
                f"Question: {example['question']}\n"
                f"Available Agents: {example['available_agents']}\n\n"
                f"<analysis>{example['analysis']}</analysis>\n"
                f"<plan>{json.dumps(example['plan'], ensure_ascii=False)}</plan>\n"
            )
        return "\n".join(examples_str)

    def _format_available_agents(self, agents: list[AgentInfo]) -> str:
        agents_str = []
        for agent in agents:
            agents_str.append(
                f"- {agent.name}: {agent.desc}\n  Best for: {agent.strengths}\n"
                if agent.strengths
                else f"  Weaknesses: {agent.weaknesses}\n"
                if agent.weaknesses
                else ""
            )
        return "\n".join(agents_str)
