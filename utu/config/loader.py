from typing import TypeVar, Type, Literal, Callable

from pydantic import BaseModel
from dotenv import load_dotenv
from omegaconf import OmegaConf, DictConfig
from hydra import compose, initialize

load_dotenv()
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

class Config(BaseModel):
    model: ModelConfig
    agent: AgentConfig
    toolkits: dict[str, ToolkitConfig] = {}


class ConfigLoader:
    config_path = "../../configs"
    version_base = "1.3"

    @classmethod
    def _load_config_to_dict(cls, name: str = "default") -> DictConfig:
        with initialize(config_path=cls.config_path, version_base=cls.version_base):
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
    def load_toolkit_config(cls, name: str = "default") -> ToolkitConfig:
        cfg = cls._load_config_to_dict(name)
        return ToolkitConfig(**cfg)
