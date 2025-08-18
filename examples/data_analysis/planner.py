import pathlib
import re

from utu.agents.orchestra.common import CreatePlanResult, OrchestraTaskRecorder
from utu.agents.orchestra.planner import PlannerAgent
from utu.config import AgentConfig
from utu.tools import TabularDataToolkit
from utu.utils import get_jinja_env


class DAPlannerAgent(PlannerAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.jinja_env = get_jinja_env(
            pathlib.Path(__file__).parent.parent.parent / "utu" / "agents" / "orchestra" / "prompts"
        )

    async def create_plan(self, task_recorder: OrchestraTaskRecorder) -> CreatePlanResult:
        background_info = await self._get_background_info(task_recorder)
        sp = self.jinja_env.get_template("planner_sp.j2").render(
            planning_examples=self._format_planner_examples(self.planner_examples)
        )
        up = self.jinja_env.get_template("planner_up.j2").render(
            available_agents=self._format_available_agents(self.available_agents),
            question=task_recorder.task,
            background_info=background_info,
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
        info_str += (
            "\n**Note**: These background information is invisible to other agents, "
            "but can help you to make better plan. So your plan should be based on the assumption "
            "that the agents is initially unaware of this information."
        )
        return info_str

    def _extract_file_path(self, task: str) -> str:
        """Extract file path from the task description."""
        match = re.search(r"`([^`]+)`", task)
        if match:
            return match.group(1).strip()
        return ""
