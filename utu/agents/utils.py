from dataclasses import dataclass, field

from ..config import AgentConfig


class Base:
    def __init__(self, config: AgentConfig):
        self.config = config

    async def build(self):
        pass


@dataclass
class NextTaskResult:
    task: str = ""
    is_finished: bool = False
    todo: list[str] = field(default_factory=list)

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[planner] {self.todo}"}]


@dataclass
class SearchResult:
    output: str
    trajectory: list[dict]


@dataclass
class AnalysisResult:
    output: str

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[analysis] {self.output}"}]

