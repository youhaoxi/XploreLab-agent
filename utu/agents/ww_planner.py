import requests

from .utils import Base, NextTaskResult, Task
from ..config import AgentConfig


class DummayPlannerAgent(Base):
    async def get_next_task(self, query=None, prev_subtask_result=None, trace_id=None) -> NextTaskResult:
        """ get next task to execute """
        if prev_subtask_result:
            return NextTaskResult(is_finished=True)
        return NextTaskResult(task=Task(agent="SearchAgent", task=query), todo=[query])


class PlannerAgent(Base):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.base_url = "http://9.134.241.185:10101"

    async def get_next_task(self, query: str=None, prev_subtask_result: str=None, trace_id: str=None) -> NextTaskResult:
        next_task: Task = None
        if not prev_subtask_result:
            planning_data = {
                "session_id": trace_id,
                "question": query,
                "background_info": ""  # TODO: add background info
            }
            response = requests.post(f"{self.base_url}/planning", json=planning_data)
            response.raise_for_status()
            result = response.json()
            next_task = Task(**result["next_step"])
            return NextTaskResult(task=next_task, todo=result["plan"])
        else:
            update_data = {
                "session_id": trace_id,
                "task": next_task.task,
                "task_results": prev_subtask_result
            }
            response = requests.post(f"{self.base_url}/update_planning", json=update_data)
            response.raise_for_status()
            result = response.json()
            next_task = Task(**result["next_step"]) if (not result["task_finished"]) else None
            return NextTaskResult(task=next_task, is_finished=result["task_finished"], todo=result["plan"])
