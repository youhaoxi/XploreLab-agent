import json
import re
from dataclasses import dataclass, field
from typing import Literal

from openai.types.responses import EasyInputMessageParam

from ...config import AgentConfig
from ...utils import AgentsUtils, FileUtils, get_logger
from ..common import DataClassWithStreamEvents
from ..llm_agent import LLMAgent

logger = get_logger(__name__)


@dataclass
class Task:
    agent_name: str
    task: str
    result: str | None = None
    is_last_task: bool = False  # whether this task is the last task of the plan


@dataclass
class Plan:
    input: str = ""
    analysis: str = ""
    tasks: list[Task] = field(default_factory=list)

    def format_tasks(self) -> str:
        tasks = [{"name": t.agent_name, "task": t.task} for t in self.tasks]
        return json.dumps(tasks, ensure_ascii=False)

    def format_plan(self) -> str:
        return f"<analysis>{self.analysis}</analysis>\n<plan>{self.format_tasks()}</plan>"


@dataclass
class Recorder(DataClassWithStreamEvents):
    # current main task
    input: str = ""  # current user input
    final_output: str = None  # final output to `input`. Naming consistent with @agents.RunResult
    trajectories: list = field(default_factory=list)  # trajs corresponding to `input`
    trace_id: str = ""

    # planning
    tasks: list[Task] = None
    current_task_id: int = 0

    # history
    history_plan: list[EasyInputMessageParam] = field(default_factory=list)
    history_messages: list[EasyInputMessageParam] = field(default_factory=list)

    def get_plan_str(self) -> str:
        return "\n".join([f"{i}. {t.task}" for i, t in enumerate(self.tasks, 1)])

    def get_trajectory_str(self) -> str:
        traj = []
        for t in self.tasks:
            if t.result is None:
                break
            traj.append(f"<task>{t.task}</task>\n<output>{t.result}</output>")
        return "\n".join(traj)

    def add_plan(self, plan: Plan) -> None:
        self.tasks = plan.tasks
        self.history_plan.extend(
            [
                {"role": "user", "content": f"<question>{plan.input}</question>"},
                {"role": "assistant", "content": plan.format_plan()},
            ]
        )

    def add_final_output(self, final_output: str) -> None:
        self.final_output = final_output
        self.history_messages.extend(
            [
                {"role": "user", "content": "self.input"},
                {"role": "assistant", "content": final_output},
            ]
        )

    def new(self, input: str = None, trace_id: str = None) -> "Recorder":
        """Create a new recorder with the same history -- for multi-turn chat."""
        new_recorder = Recorder(input=input, trace_id=trace_id)
        new_recorder.history_plan = self.history_plan.copy()
        return new_recorder


@dataclass
class OrchestratorStreamEvent:
    name: Literal["plan.start", "plan.done"]
    item: dict | list | str | None = None
    type: Literal["orchestrator_stream_event"] = "orchestrator_stream_event"


class Orchestrator:
    """Task planner that handles task decomposition."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.prompts = FileUtils.load_prompts("agents/orchestrator/chain.yaml")

        examples_path = self.config.orchestrator_config.get("examples_path", "plan_examples/chain.json")
        self.planner_examples = FileUtils.load_json_data(examples_path)
        self.additional_instructions = self.config.orchestrator_config.get("additional_instructions", "")

    async def create_plan(self, recorder: Recorder) -> None:
        """Plan tasks based on the overall task and available agents."""
        # format examples to string. example: {question, available_agents, analysis, plan}
        examples_str = []
        for example in self.planner_examples:
            examples_str.append(
                f"<question>{example['question']}</question>\n"
                f"<available_agents>{example['available_agents']}</available_agents>\n"
                f"<analysis>{example['analysis']}</analysis>\n"
                f"<plan>{json.dumps(example['plan'], ensure_ascii=False)}</plan>"
            )
        examples_str = "\n".join(examples_str)
        sp = FileUtils.get_jinja_template_str(self.prompts["orchestrator_sp"]).render(planning_examples=examples_str)
        llm = LLMAgent(
            name="orchestrator",
            instructions=sp,
            model_config=self.config.orchestrator_model,
        )
        up = FileUtils.get_jinja_template_str(self.prompts["orchestrator_up"]).render(
            additional_instructions=self.additional_instructions,
            question=recorder.input,
            available_agents=self.config.orchestrator_workers_info,
            # background_info=await self._get_background_info(recorder),
        )
        if recorder.history_plan:
            input = recorder.history_plan + [{"role": "user", "content": up}]
        else:
            input = up
        recorder._event_queue.put_nowait(OrchestratorStreamEvent(name="plan.start"))
        res = llm.run_streamed(input)
        await self._process_streamed(res, recorder)
        plan = self._parse(res.final_output, recorder)
        recorder._event_queue.put_nowait(OrchestratorStreamEvent(name="plan.done", item=plan))
        # set tasks & record trajectories
        recorder.add_plan(plan)
        recorder.trajectories.append(AgentsUtils.get_trajectory_from_agent_result(res, "orchestrator"))

    def _parse(self, text: str, recorder: Recorder) -> Plan:
        match = re.search(r"<analysis>(.*?)</analysis>", text, re.DOTALL)
        analysis = match.group(1).strip() if match else ""

        match = re.search(r"<plan>\s*\[(.*?)\]\s*</plan>", text, re.DOTALL)
        plan_content = match.group(1).strip()
        tasks: list[Task] = []
        task_pattern = r'\{"name":\s*"([^"]+)",\s*"task":\s*"([^"]+)"\s*\}'
        task_matches = re.findall(task_pattern, plan_content, re.IGNORECASE)
        for agent_name, task_desc in task_matches:
            tasks.append(Task(agent_name=agent_name, task=task_desc))
        # check validity
        assert len(tasks) > 0, "No tasks parsed from plan"
        tasks[-1].is_last_task = True  # FIXME: polish this
        return Plan(input=recorder.input, analysis=analysis, tasks=tasks)

    async def get_next_task(self, recorder: Recorder) -> Task | None:
        """Get the next task to be executed."""
        if not recorder.tasks:
            raise ValueError("No tasks available. Please create a plan first.")
        if recorder.current_task_id >= len(recorder.tasks):
            return None
        task = recorder.tasks[recorder.current_task_id]
        recorder.current_task_id += 1
        return task

    async def _process_streamed(self, res: DataClassWithStreamEvents, recorder: Recorder):
        async for event in res.stream_events():
            recorder._event_queue.put_nowait(event)
