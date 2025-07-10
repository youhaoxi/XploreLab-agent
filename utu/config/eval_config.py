import os
from typing import Literal

from .agent_config import AgentConfig
from .base_config import ConfigBaseModel


class EvalConfig(ConfigBaseModel):
    exp_id: str = "default"
    
    # TODO: seperate config into subconfigs: data/output/rollout/judge/agent
    db_url: str = os.getenv("DB_URL", "sqlite:///evaluation_samples.db")
    # input
    dataset: str                 # built-in dataset name or custom dataset path
    type: Literal["single", "mixed"]  # 数据集里只包含单独的benchmark数据，还是包含多个benchmarks  
    question_field: str
    gt_field: str
    
    # rollout
    max_turns: int  # FIXME: this is not used now!
    concurrency: int             # rollout parallelism
    
    # judgement
    judge_model: str
    judge_api_key: str
    judge_model_base_url: str
    judge_concurrency: int       # judgement parallelism
    judge_max_tokens: int
    eval_method: str = None # 使用什么benchmark的评估方法（"GAIA", "BrowseCamp", ...)

    # agent
    agent: AgentConfig | None = None
