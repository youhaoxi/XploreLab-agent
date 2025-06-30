from typing import TypeVar, Type, Literal, Callable

from pydantic import BaseModel
from omegaconf import OmegaConf, DictConfig
from hydra import compose, initialize

TConfig = TypeVar("TConfig", bound=BaseModel)


class ModelConfig(BaseModel):
    api_key: str
    base_url: str
    model: str

class AgentConfig(BaseModel):
    name: str
    instructions: str | Callable

class ToolkitConfig(BaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str
    activated_tools: list[str] | None = None
    config: dict | None = None

class EvalConfig(BaseModel):
    """
    dataset: str   # 可以是内置数据集 (GAIA, BrowseCamp) 或者自定义数据文件路径
    output_file: str = "eval_result.jsonl"  # 输出形式, 可以是其他格式
    metrics_file: str = "metrics.json"  # 评估指标文件
    concurrency: int = 16  # rollout parallelism
    judge_concurrency: int = 16  # judgement parallelism
    max_turns: int = 10    # limit of #actions
    """
    # dataset config
    dataset: str
    type: Literal["single", "mixed"]  # 数据集里只包含单独的benchmark数据，还是包含多个benchmarks  
    question_field: str
    gt_field: str
    # output config
    output_file: str
    metrics_file: str
    judge_output_file: str
    # concurrency config
    thread_pool_size: int
    concurrency: int
    max_turns: int
    # below for judgement
    judge_model: str
    judge_api_key: str
    judge_model_base_url: str
    judge_concurrency: int
    judge_max_tokens: int

    eval_method: str = None # 使用什么benchmark的评估方法（"GAIA", "BrowseCamp", ...)

class Config(BaseModel):
    model: ModelConfig
    agent: AgentConfig
    toolkits: dict[str, ToolkitConfig] = {}


class ConfigLoader:
    config_path = "../../configs"
    version_base = "1.3"

    @classmethod
    def _load_config_to_dict(cls, name: str = "default", config_path: str = None) -> DictConfig:
        config_path = config_path or cls.config_path
        with initialize(config_path=config_path, version_base=cls.version_base):
            cfg = compose(config_name=name)
            OmegaConf.resolve(cfg)
        return cfg

    @classmethod
    def _load_config_to_cls(cls, name: str, config_type: Type[TConfig] = None) -> TConfig:
        # TESTING
        cfg = cls._load_config_to_dict(name)
        return config_type(**cfg)

    @classmethod
    def load_config(cls, name: str = "default") -> Config:
        cfg = cls._load_config_to_dict(name)
        return Config(**cfg)

    @classmethod
    def load_toolkit_config(cls, name: str = "search") -> ToolkitConfig:
        cfg = cls._load_config_to_dict(name, config_path="../../configs/tools")
        return ToolkitConfig(**cfg)

    @classmethod
    def load_model_config(cls, name: str = "base") -> ModelConfig:
        cfg = cls._load_config_to_dict(name, config_path="../../configs/model")
        return ModelConfig(**cfg)
    
    @classmethod
    def load_eval_config(cls, name: str = "default") -> EvalConfig:
        cfg = cls._load_config_to_dict(name, config_path="../../configs/eval")
        return EvalConfig(**cfg)
