from ..utils import Base, NextTaskResult, Task


class DummyPlannerAgent(Base):
    async def get_next_task(self, query=None, prev_subtask_result=None, trace_id=None) -> NextTaskResult:
        """get next task to execute"""
        if prev_subtask_result:
            return NextTaskResult(is_finished=True)
        return NextTaskResult(task=Task(agent_name="SearchAgent", task=query), todo=[query])
