from dataclasses import dataclass, field

from ..config import AgentConfig
from .simple_agent import SimpleAgent
from ..eval.common import get_trajectory_from_agent_result


class Base:
    def __init__(self, config: AgentConfig):
        self.config = config

    async def build(self):
        pass

@dataclass
class SearchResult:
    output: str
    trajectory: list[dict]

class SearcherAgent(Base):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.agent = SimpleAgent(config)  # v0

    async def build(self):
        await self.agent.build()

    async def research(self, subtask: str) -> SearchResult:
        """search webpages for a specific subtask, return a report """
        run_result = await self.agent.run(subtask)
        return SearchResult(
            output=run_result.final_output,
            trajectory=get_trajectory_from_agent_result(run_result),
        )


@dataclass
class NextTaskResult:
    task: str = ""
    is_finished: bool = False
    todo: list[str] = field(default_factory=list)

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[planner] {self.todo}"}]

class PlannerAgent(Base):
    async def get_next_task(self, query=None, prev_subtask_result=None) -> NextTaskResult:
        """ get next task to execute """
        if prev_subtask_result:
            return NextTaskResult(is_finished=True)
        return NextTaskResult(task=query, todo=[query])


@dataclass
class AnalysisResult:
    output: str

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[analysis] {self.output}"}]


class AnalysisAgent(Base):
    async def analyze(self, task_records: list[tuple[NextTaskResult, SearchResult]]) -> AnalysisResult:
        """analyze the result of a subtask, return a report"""
        return AnalysisResult(output=task_records[-1][1].output)
