from typing import Optional

from pydantic import BaseModel, Field


class RunResult(BaseModel):
    final_output: str
    trajectory: list[dict]  # [{"agent": "SearchAgent", "trajectory": [{"role": "user", "content": "..."}, ...]}, ...]
    trace_id: str = ""


class AgentInfo(BaseModel):
    """Subagent information (for planner)"""
    name: str
    desc: str
    strengths: str
    weaknesses: str


class Subtask(BaseModel):
    agent_name: str
    task: str
    completed: Optional[bool] = None

class CreatePlanResult(BaseModel):
    analysis: str = ""
    todo: list[Subtask] = Field(default_factory=list)

    @property
    def trajectory(self):
        todos_str = []
        for i,subtask in enumerate(self.todo, 1):
            todos_str.append(f"{i}. {subtask.task} ({subtask.agent_name})")
        todos_str = "\n".join(todos_str)
        return {
            "agent": "planner",
            "trajectory": [
                {"role": "assistant", "content": self.analysis},
                {"role": "assistant", "content": todos_str}
            ]
        }


class WorkerResult(BaseModel):
    task: str
    output: str
    trajectory: dict
    search_results: list[dict] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    output: str

    @property
    def trajectory(self):
        return {
            "agent": "analysis",
            "trajectory": [{"role": "assistant", "content": self.output}]
        }


class TaskRecorder:
    def __init__(self, task: str, trace_id: str):
        self.task = task
        self.trace_id = trace_id
        self.trajectories: list = []
        self.task_records: list[WorkerResult] = []
        self.plan: CreatePlanResult = None

    def set_plan(self, plan: CreatePlanResult):
        self.plan = plan
        self.trajectories.append(plan.trajectory)

    def add_worker_result(self, result: WorkerResult):
        self.task_records.append(result)
        self.trajectories.append(result.trajectory)

    def add_reporter_result(self, result: AnalysisResult):
        self.trajectories.append(result.trajectory)

    def get_plan_str(self) -> str:
        return "\n".join([
            f"{i}. {t.task}" for i, t in enumerate(self.plan.todo, 1)
        ])

    def get_trajectory_str(self) -> str:
        return "\n".join([
            f"<subtask>{t.task}</subtask>\n<output>{r.output}</output>" 
            for i, (r, t) in enumerate(zip(self.task_records, self.plan.todo), 1)
        ])
