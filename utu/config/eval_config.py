import os
from typing import Literal

from pydantic import Field

from .agent_config import AgentConfig, ModelConfigs
from .base_config import ConfigBaseModel


class DataConfig(ConfigBaseModel):
    """Data config"""

    dataset: str
    """Built-in dataset name or custom dataset path"""
    type: Literal["single", "mixed"]
    """Whether the dataset contains only single benchmark data or multiple benchmarks"""
    question_field: str
    """Question field name in the dataset"""
    gt_field: str
    """Ground truth field name in the dataset"""


class EvalConfig(ConfigBaseModel):
    """Evaluation config"""

    exp_id: str = "default"
    """Experiment ID"""

    # data
    db_url: str = os.getenv("DB_URL", "sqlite:///tesxt.db")
    """Database URL"""
    data: DataConfig = None
    """Data config"""

    # rollout
    agent: AgentConfig | None = None
    """Agent config for rollout"""
    concurrency: int
    """Rollout parallelism"""

    # judgement
    judge_model: ModelConfigs = Field(default_factory=ModelConfigs)
    """Judge model config"""
    judge_concurrency: int
    """Judgement parallelism"""
    eval_method: str = None
    """Evaluation method"""
