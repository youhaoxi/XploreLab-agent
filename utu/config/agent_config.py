from typing import Callable, Optional
from typing_extensions import Literal

from pydantic import Field, ConfigDict
from agents import ModelSettings

from .base_config import ConfigBaseModel


DEFAULT_INSTRUCTIONS = "You are a helpful assistant."


class ModelConfig(ConfigBaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str

    temperature: float | None = None
    top_p: float | None = None
    # ...


class ModelSettingsConfig(ConfigBaseModel, ModelSettings):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    parallel_tool_calls: bool | None = False  # default to False

class ProfileConfig(ConfigBaseModel):
    name: Optional[str] = "default"
    instructions: Optional[str | Callable] = DEFAULT_INSTRUCTIONS


class ToolkitConfig(ConfigBaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str | None = None
    activated_tools: list[str] | None = None
    config: dict | None = Field(default_factory=dict)
    config_llm: ModelConfig | None = None

class ContextManagerConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)

class AgentConfig(ConfigBaseModel):
    type: Literal["simple", "simple_env"] = "simple"  # FIXME: 
    model: ModelConfig
    model_settings: ModelSettingsConfig = Field(default_factory=ModelSettingsConfig)
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    context_manager: ContextManagerConfig = Field(default_factory=ContextManagerConfig)
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    max_turns: int = 20
