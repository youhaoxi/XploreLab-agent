from typing import TypeVar

from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel

from .agent_config import AgentConfig, ToolkitConfig
from .eval_config import EvalConfig
from .model_config import ModelConfigs

TConfig = TypeVar("TConfig", bound=BaseModel)


class ConfigLoader:
    """Config loader"""

    config_path = "../../configs"
    version_base = "1.3"

    @classmethod
    def _load_config_to_dict(cls, name: str = "default", config_path: str = None) -> DictConfig:
        config_path = config_path or cls.config_path
        with initialize(config_path=config_path, version_base=cls.version_base):
            cfg = compose(config_name=name)
            OmegaConf.resolve(cfg)
        return cfg

    # @classmethod
    # def _load_config_to_cls(cls, name: str, config_type: Type[TConfig] = None) -> TConfig:
    #     # TESTING
    #     cfg = cls._load_config_to_dict(name)
    #     return config_type(**cfg)

    @classmethod
    def load_agent_config(cls, name: str = "default") -> AgentConfig:
        """Load agent config from /configs/agents"""
        cfg = cls._load_config_to_dict(name, config_path="../../configs/agents")
        return AgentConfig(**cfg)

    @classmethod
    def load_toolkit_config(cls, name: str = "search") -> ToolkitConfig:
        """Load toolkit config from /configs/agents/tools"""
        cfg = cls._load_config_to_dict(name, config_path="../../configs/agents/tools")
        return ToolkitConfig(**cfg)

    @classmethod
    def load_model_config(cls, name: str = "base") -> ModelConfigs:
        """Load model config from /configs/agents/model"""
        cfg = cls._load_config_to_dict(name, config_path="../../configs/agents/model")
        return ModelConfigs(**cfg)

    @classmethod
    def load_eval_config(cls, name: str = "default") -> EvalConfig:
        """Load eval config from /configs"""
        if not name.startswith("eval/"):
            name = "eval/" + name
        cfg = cls._load_config_to_dict(name, config_path="../../configs")
        return EvalConfig(**cfg)
