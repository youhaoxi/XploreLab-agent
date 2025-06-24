from typing import TypeVar, Type, Literal, Callable

from pydantic import BaseModel
from dotenv import load_dotenv
from omegaconf import OmegaConf

from ..utils import DIR_ROOT

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
    toolkits: list[ToolkitConfig] = []


def load_config(config_path: str, config_type: Type[TConfig] = Config) -> TConfig:
    config = OmegaConf.load(config_path)
    config = OmegaConf.to_container(config, resolve=True)
    structed_config = config_type(**config)
    return structed_config

def load_config_by_name(name: str = "default") -> Config:
    if name.endswith(".yaml"): name = name[:-5]
    config_path = DIR_ROOT / "configs" / f"{name}.yaml"
    return load_config(config_path)
