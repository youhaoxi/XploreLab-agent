import requests
import asyncio

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
        self.base_url = "http://9.134.243.10:10101"
        self.traceid_to_nexttask: dict[str, Task] = {}

    async def async_request_post(self, url: str, data: dict) -> dict:
        # use thread to avoid blocking
        response = await asyncio.to_thread(requests.post, url, json=data)
        response.raise_for_status()
        return response.json()

    async def get_next_task(self, query: str=None, prev_subtask_result: str=None, trace_id: str=None) -> NextTaskResult:
        next_task: Task = None
        if not prev_subtask_result:
            planning_data = {
                "session_id": trace_id,
                "question": query,
                "background_info": ""  # TODO: add background info
            }
            result = await self.async_request_post(f"{self.base_url}/planning", planning_data)
            next_task = Task(**result["next_step"])
            self.traceid_to_nexttask[trace_id] = next_task
            return NextTaskResult(task=next_task, todo=result["plan"])
        else:
            next_task = self.traceid_to_nexttask.get(trace_id)
            update_data = {
                "session_id": trace_id,
                "task": next_task.task,
                "task_results": prev_subtask_result
            }
            result = await self.async_request_post(f"{self.base_url}/update_planning", update_data)
            next_task = Task(**result["next_step"]) if (not result["task_finished"]) else None
            self.traceid_to_nexttask[trace_id] = next_task
            return NextTaskResult(task=next_task, is_finished=result["task_finished"], todo=result["plan"])
