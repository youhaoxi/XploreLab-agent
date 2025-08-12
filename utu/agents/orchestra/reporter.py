from .common import AnalysisResult, TaskRecorder
from ...config import AgentConfig
from ...utils import SimplifiedAsyncOpenAI


TEMPLATE = """Please answer the original question based on the trajectory of the subtasks.

## input
<question>
{question}
</question>
<trajectory>
{trajectory}
</trajectory>

## rules
- language: your response should be in the same language as the question.

## output format
Explanation: {{your explanation for your final answer}}
Exact Answer: {{your succinct, final answer}}
Confidence: {{your confidence score between 0% and 100% for your answer}}
""".strip()


class ReporterAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = SimplifiedAsyncOpenAI(**self.config.reporter_model.model_params.model_dump())

    async def build(self):
        pass

    async def report(self, task_recorder: TaskRecorder) -> AnalysisResult:
        """analyze the result of a subtask, return a report"""
        query = TEMPLATE.format(
            question=task_recorder.task,
            trajectory=task_recorder.get_trajectory_str()
        )
        response = await self.llm.query_one(messages=query, **self.config.reporter_model.model_params.model_dump())
        return AnalysisResult(output=response)
