from dataclasses import dataclass, field

from ..config import AgentConfig


class Base:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.trace_id: str = None

    async def build(self):
        pass

    def set_trace_id(self, trace_id: str):
        self.trace_id = trace_id


@dataclass
class Task:
    agent: str
    task: str

@dataclass
class NextTaskResult:
    task: Task = None
    is_finished: bool = False
    todo: list[dict] = field(default_factory=list)

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[planner] {self.todo}"}]


@dataclass
class SearchResult:
    output: str
    trajectory: list[dict]
    search_results: list[dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    output: str

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[analysis] {self.output}"}]
