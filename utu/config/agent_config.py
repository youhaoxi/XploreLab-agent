from typing import Callable, Optional
from typing_extensions import Literal

from pydantic import Field, ConfigDict
from agents import ModelSettings

from .base_config import ConfigBaseModel


DEFAULT_INSTRUCTIONS = "You are a helpful assistant."


class ModelProviderConfig(ConfigBaseModel):
    model: str
    base_url: str | None = None
    api_key: str | None = "xxx"


class ModelSettingsConfig(ConfigBaseModel, ModelSettings):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    # parallel_tool_calls: bool | None = False  # default to False?


class ModelConfigs(ConfigBaseModel):
    model_provider: ModelProviderConfig
    model_settings: ModelSettingsConfig = Field(default_factory=ModelSettingsConfig)

class ProfileConfig(ConfigBaseModel):
    name: Optional[str] = "default"
    instructions: Optional[str | Callable] = DEFAULT_INSTRUCTIONS


class ToolkitConfig(ConfigBaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str | None = None
    activated_tools: list[str] | None = None
    config: dict | None = Field(default_factory=dict)
    config_llm: ModelProviderConfig | None = None

class ContextManagerConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)

class AgentConfig(ConfigBaseModel):
    type: Literal["simple", "simple_env"] = "simple"  # FIXME: 
    model: ModelConfigs = Field(default_factory=ModelConfigs)
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    context_manager: ContextManagerConfig = Field(default_factory=ContextManagerConfig)
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    max_turns: int = 20
