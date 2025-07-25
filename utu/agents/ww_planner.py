from .utils import Base, NextTaskResult


class PlannerAgent(Base):
    async def get_next_task(self, query=None, prev_subtask_result=None) -> NextTaskResult:
        """ get next task to execute """
        if prev_subtask_result:
            return NextTaskResult(is_finished=True)
        return NextTaskResult(task=query, todo=[query])

