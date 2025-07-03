from typing import Callable, Optional
from typing_extensions import Literal

from pydantic import Field

from .base_config import ConfigBaseModel


DEFAULT_INSTRUCTIONS = "You are a helpful assistant."


class ModelConfig(ConfigBaseModel):
    api_key: str
    base_url: str
    model: str

class ProfileConfig(ConfigBaseModel):
    name: Optional[str] = "default"
    instructions: Optional[str | Callable] = DEFAULT_INSTRUCTIONS


class ToolkitConfig(ConfigBaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str | None = None
    activated_tools: list[str] | None = None
    config: dict | None = None
    config_llm: ModelConfig | None = None


class AgentConfig(ConfigBaseModel):
    type: Literal["simple"] = "simple"
    model: ModelConfig
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    
