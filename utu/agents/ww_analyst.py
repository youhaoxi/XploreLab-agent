from .utils import Base, AnalysisResult, NextTaskResult, SearchResult


class AnalysisAgent(Base):
    async def analyze(self, task_records: list[tuple[NextTaskResult, SearchResult]], trace_id: str = None) -> AnalysisResult:
        """analyze the result of a subtask, return a report"""
        return AnalysisResult(output=task_records[-1][1].output)
