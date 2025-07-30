from .utils import Base, AnalysisResult, NextTaskResult, SearchResult
from ...config import AgentConfig
from ...utils import SimplifiedAsyncOpenAI


TEMPLATE = """Please answer the original question based on the trajectory of the subtasks.
<question>
{question}
</question>
<trajectory>
{trajectory}
</trajectory>

Your response should be in the following format:
Explanation: {{your explanation for your final answer}}
Exact Answer: {{your succinct, final answer}}
Confidence: {{your confidence score between 0% and 100% for your answer}}
""".strip()


class DummyAnalysisAgent(Base):
    async def analyze(self, input: str, task_records: list[tuple[NextTaskResult, SearchResult]], trace_id: str = None) -> AnalysisResult:
        """analyze the result of a subtask, return a report"""
        return AnalysisResult(output=task_records[-1][1].output)


class AnalysisAgent(Base):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm = SimplifiedAsyncOpenAI()

    async def analyze(self, input: str, task_records: list[tuple[NextTaskResult, SearchResult]], trace_id: str = None) -> AnalysisResult:
        """analyze the result of a subtask, return a report"""
        query = TEMPLATE.format(
            question=input,
            trajectory="\n".join([f"{record[0].task.task}\n{record[1].output}" for record in task_records])
        )
        response = await self.llm.query_one(messages=query)
        return AnalysisResult(output=response)
