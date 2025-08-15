import os
from typing import Literal

from pydantic import Field

from .agent_config import AgentConfig, ModelConfigs
from .base_config import ConfigBaseModel


class DataConfig(ConfigBaseModel):
    dataset: str  # built-in dataset name or custom dataset path
    type: Literal["single", "mixed"]  # 数据集里只包含单独的benchmark数据，还是包含多个benchmarks
    question_field: str
    gt_field: str


class EvalConfig(ConfigBaseModel):
    # TODO: seperate config into subconfigs: data/output/rollout/judge/agent
    exp_id: str = "default"

    # data
    db_url: str = os.getenv("DB_URL", "sqlite:///evaluation_samples.db")
    data: DataConfig = None

    # rollout
    agent: AgentConfig | None = None
    concurrency: int  # rollout parallelism

    # judgement
    judge_model: ModelConfigs = Field(default_factory=ModelConfigs)
    judge_concurrency: int  # judgement parallelism
    eval_method: str = None  # 使用什么benchmark的评估方法（"GAIA", "BrowseCamp", ...)
