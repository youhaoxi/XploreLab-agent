from collections.abc import Callable
from typing import Literal

from pydantic import Field

from .base_config import ConfigBaseModel
from .model_config import ModelConfigs

DEFAULT_INSTRUCTIONS = "You are a helpful assistant."


class ProfileConfig(ConfigBaseModel):
    name: str | None = "default"
    instructions: str | Callable | None = DEFAULT_INSTRUCTIONS


class ToolkitConfig(ConfigBaseModel):
    """Toolkit config."""

    mode: Literal["builtin", "mcp"] = "builtin"
    name: str | None = None
    activated_tools: list[str] | None = None
    """Activated tools, if None, all tools will be activated."""
    config: dict | None = Field(default_factory=dict)
    """Toolkit config."""
    config_llm: ModelConfigs | None = None
    """LLM config if used in toolkit."""


class ContextManagerConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)


class EnvConfig(ConfigBaseModel):
    name: str | None = None
    config: dict | None = Field(default_factory=dict)


class AgentConfig(ConfigBaseModel):
    """Overall agent config"""

    type: Literal["simple", "orchestra"] = "simple"
    """Agent type, "simple" or "orchestra". """

    model: ModelConfigs = Field(default_factory=ModelConfigs)
    """Model config, with model_provider, model_settings, model_params"""
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    """Agent profile config"""
    context_manager: ContextManagerConfig = Field(default_factory=ContextManagerConfig)
    """Context manager config"""
    env: EnvConfig = Field(default_factory=EnvConfig)
    """Env config"""
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    """Toolkits config"""
    max_turns: int = 20
    """Max turns"""

    planner_model: ModelConfigs = Field(default_factory=ModelConfigs)
    """Planner model config"""
    planner_config: dict = Field(default_factory=dict)
    """Planner config (dict)\n
    - `examples_path`: path to planner examples json file"""
    workers: dict[str, "AgentConfig"] = Field(default_factory=dict)
    """Workers config"""
    workers_info: list[dict] = Field(default_factory=list)
    """Workers info, list of {name, desc, strengths, weaknesses}\n
    - `name`: worker name
    - `desc`: worker description
    - `strengths`: worker strengths
    - `weaknesses`: worker weaknesses"""
    reporter_model: ModelConfigs = Field(default_factory=ModelConfigs)
    """Reporter model config"""
    reporter_config: dict = Field(default_factory=dict)
    """Reporter config (dict)\n
    - `template_path`: template Jinja2 file path, with `question` and `trajectory` variables"""
