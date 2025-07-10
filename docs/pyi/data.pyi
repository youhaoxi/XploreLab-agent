import abc
from typing import Optional, Literal

from pydantic import BaseModel, Field

from utu.config import EvalConfig

""" 
1. Sample (EvaluationSample): 单条数据建模, 伴随 eval 整个生命周期, 通过 stage 区分不同的阶段;
2. Processer: 封装针对单一数据集特有的逻辑, 包括 load_data, SP, judge, metric计算 等;
    下面继承不同的子类来处理不同数据集
3. DataManager: 封装数据管理逻辑. 加载/筛选/保存/更新数据;
4. Benchmark: 封装整个评估/实验流程, 包括 rollout, judge, stat 等;

"""
# datapoint
class Sample(BaseModel):
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


class BaseProcesser(abc.ABC):
    def __init__(self, config: EvalConfig) -> None:
        ...
    def get_instructions(self) -> str:
        """ Return the instructions for the agent. """
    # async def load(self) -> list[Sample]:
    #     """ Load and process data. """
    async def preprocess(self, data: list[Sample]) -> list[Sample]:
        """ Preprocess the raw dataset. e.g. augment the question. """
    async def judge_one(self, data: Sample) -> Sample:
        """ Judge a single sample. """
    async def stat(self, judged_data: list[Sample]) -> "EvaluationResult":
        """ Get metrics. """


class DataManager:
    def load(self) -> list[Sample]:
        # """Load the dataset. Preprocessing"""
        """ Load the raw dataset. """
    def save(self, **kwargs) -> None:
        """Save the dataset. e.g. to db"""
    def get_samples(self, stage: Literal["init", "rollout", "judged"] = None) -> list[Sample]:
        """Get samples of specified stage from the dataset. -> for steps in Benchmark."""


class Benchmark:
    def __init__(self, config: EvalConfig) -> None:
        ...

    async def main(self):
        await self.preprocess()
        await self.rollout()
        await self.judge()
        await self.stat()

    def preprocess(self) -> list[Sample]:
        """Preprocess the raw dataset. e.g. augment the question."""
    async def rollout(self) -> dict:
        """Step 1: Rollout the benchmark. Return rollout results desc."""
    async def judge(self) -> dict:
        """Step 2: Judge the rollout results. Return judge results desc. e.g. EvaluationResult"""
    async def stat(self):
        """Step 3: Stat the results."""
