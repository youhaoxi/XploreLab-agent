from typing import Literal

from pydantic import BaseModel

from .agent_config import AgentConfig


class EvalConfig(BaseModel):
    exp_id: str = "default"
    
    # input
    dataset: str                 # built-in dataset name or custom dataset path
    type: Literal["single", "mixed"]  # 数据集里只包含单独的benchmark数据，还是包含多个benchmarks  
    question_field: str
    gt_field: str
    
    # output
    output_file: str
    metrics_file: str
    judge_output_file: str
    
    # rollout
    max_turns: int
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