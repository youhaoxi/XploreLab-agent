""" 
数据封装 v0.2
    整体调用 (runner.py): 调用 Eval, DataManager 两个组件. 
        流程: load data -> rollout -> evaluate & stat
        其中 DataManager 模块负责保存数据, Eval 模块负责评估. 
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from utu.config import EvalConfig


# datapoint
class Sample(BaseModel):
    """
    A data class to represent a single evaluation sample.
    """
    # 1) base info
    source: str = ""  # dataset name
    raw_question: str = ""
    level: Optional[int] = 0  # hardness level of the question, if applicable
    augmented_question: Optional[str] = ""
    correct_answer: Optional[str] = ""
    file_name: Optional[str] = ""  # for GAIA
    stage: str = "init"  # Literal["init", "rollout", "judged]
    # 2) rollout
    response: Optional[str] = Field(default=None)
    time_cost: Optional[float] = Field(default=None)  # time cost in seconds
    trajectory: Optional[str] = Field(default=None)  # the agent's reasoning process, a list of messages
    # 3) judgement
    extracted_final_answer: Optional[str] = Field(default=None)
    judged_response: Optional[str] = Field(default=None)
    reasoning: Optional[str] = Field(default=None)
    correct: Optional[bool] = Field(default=None)
    confidence: Optional[int] = Field(default=None)
    # id
    exp_id: str = Field(default="default")


# db & processor
class DataManager:
    async def init(self) -> list[SampleSQL]:
        """Init db for certain exp_id"""
    async def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[SampleSQL]:
        """Get samples from exp_id with specified stage."""
    async def update_samples(self, samples: list[SampleSQL]|SampleSQL) -> None:
        """Update or add sample(s) to db."""
    async def delete_samples(self, samples: list[SampleSQL]|SampleSQL) -> None:
        """Delete sample(s) from db."""
class SampleSQL(SQLModel, Sample, table=True):
    __tablename__ = 'evaluation_samples'

class BaseProcesser:
    def __init__(self, config: EvalConfig) -> None:
        ...
    async def load_and_process(self, data_path: str) -> list[Sample]:
        """ Load and process data from the specified path. """
    def process_one(self, item: dict) -> Sample:
        """ Process a single item into an EvaluationSample."""

# eval
class Eval:
    # _evaluators: dict[str, BaseEval]  # cache evaluators for different benchmarks
    async def eval(self, predict_data: list[Sample]) -> list[Sample]:
        """Evaluate the predictions."""
    async def stat(self, judged_data: list[Sample]) -> EvaluationResult:
        """Get metrics"""
    def get_instructions(self) -> dict[str, str]:
        """Get instructions for each benchmark."""
        # TODO: move to datapoint?
class EvaluationResult(BaseModel):
    benchmark: str
    metrics: dict


""" 
blueprint for v0.3 
1. 保留 Sample 作为数据模型, 同步到 DB;
2. 其他组件合并为 Benchmark 类, 实现标准化的流程. 去除/集成 Processor, DataManager 等组件.
"""
class Benchmark:
    # name: str
    # description: str
    type: Literal["single", "mixed"]

    def __init__(self, config: EvalConfig) -> None:
        ...

    # data?

    # steps
    async def rollout(self) -> dict:
        """Rollout the benchmark. Return rollout results desc."""
    async def judge(self) -> dict:
        """Judge the rollout results. Return judge results desc. e.g. EvaluationResult"""

