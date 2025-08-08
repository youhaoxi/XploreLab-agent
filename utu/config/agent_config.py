from typing import Callable, Optional
from typing_extensions import Literal

from pydantic import Field

from .base_config import ConfigBaseModel
from .model_config import ModelConfigs, ModelProviderConfig


DEFAULT_INSTRUCTIONS = "You are a helpful assistant."


class ProfileConfig(ConfigBaseModel):
    name: Optional[str] = "default"
    instructions: Optional[str | Callable] = DEFAULT_INSTRUCTIONS


class ToolkitConfig(ConfigBaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str | None = None
    activated_tools: list[str] | None = None
    config: dict | None = Field(default_factory=dict)
    config_llm: ModelProviderConfig | None = None  # TODO: -> ModelConfigs

class ContextManagerConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)

class EnvConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)


class AgentConfig(ConfigBaseModel):
    type: Literal["simple", "simple_env"] = "simple"  # FIXME: 
    model: ModelConfigs = Field(default_factory=ModelConfigs)
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    context_manager: ContextManagerConfig = Field(default_factory=ContextManagerConfig)
    env: EnvConfig = Field(default_factory=EnvConfig)
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    max_turns: int = 20
