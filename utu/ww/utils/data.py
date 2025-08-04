from dataclasses import dataclass, field
from typing import Optional

from ...config import AgentConfig


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
    agent_name: str
    task: str
    completed: Optional[bool] = None

@dataclass
class NextTaskResult:
    task: Task = None
    is_finished: bool = False
    todo: list[Task] = field(default_factory=list)

    @property
    def trajectory(self):
        todos_str = []
        for i,task in enumerate(self.todo, 1):
            todos_str.append(f"{i}. {task.task} ({task.agent_name})")
        todos_str = "\n".join(todos_str)
        return [{"role": "assistant", "content": f"[planner]\n{todos_str}"}]


@dataclass
class SearchResult:
    task: str
    output: str
    trajectory: list[dict]
    search_results: list[dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    output: str

    @property
    def trajectory(self):
        return [{"role": "assistant", "content": f"[analysis] {self.output}"}]
