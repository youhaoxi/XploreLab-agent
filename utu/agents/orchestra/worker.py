from ..simple_agent import SimpleAgent
from ...config import AgentConfig
from ...utils import AgentsUtils
from .common import WorkerResult, TaskRecorder, Subtask


class BaseWorkerAgent:
    async def build(self):
        pass

    async def work(self, task_recorder: TaskRecorder, subtask: Subtask) -> WorkerResult:
        raise NotImplementedError


TEMPLATE_SEARCH = r"""Original Problem:
{problem}

Plan:
{plan}

Previous Trajectory:
{trajectory}

Current Task:
{task}
""".strip()

class SimpleWorkerAgent(BaseWorkerAgent):
    def __init__(self, config: AgentConfig):
        self.agent = SimpleAgent(config=config)

    async def build(self):
        await self.agent.build()

    async def work(self, task_recorder: TaskRecorder, subtask: Subtask) -> WorkerResult:
        """search webpages for a specific subtask, return a report """
        str_plan = task_recorder.get_plan_str()
        str_traj = task_recorder.get_trajectory_str()
        str_task = TEMPLATE_SEARCH.format(
            problem=task_recorder.task,
            plan=str_plan,
            trajectory=str_traj,
            task=subtask.task,
        )
        run_result = await self.agent.run(str_task, trace_id=task_recorder.trace_id)
        return WorkerResult(
            task=subtask.task,
            output=run_result.final_output,
            trajectory=AgentsUtils.get_trajectory_from_agent_result(run_result),
        )
