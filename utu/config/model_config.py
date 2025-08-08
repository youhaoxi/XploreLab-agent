import os
from typing_extensions import Literal

from pydantic import Field, ConfigDict
# from openai import NOT_GIVEN
from agents import ModelSettings

from .base_config import ConfigBaseModel


class ModelProviderConfig(ConfigBaseModel):
    type: Literal["chat.completions", "responses"] = os.getenv("UTU_LLM_TYPE")
    model: str = os.getenv("UTU_LLM_MODEL")
    base_url: str | None = os.getenv("UTU_LLM_BASE_URL")
    api_key: str | None = os.getenv("UTU_LLM_API_KEY")


class ModelSettingsConfig(ConfigBaseModel, ModelSettings):
    """ModelSettings in openai-agents"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class ModelParamsConfig(ConfigBaseModel):
    """Basic params shared in chat.completions and responses"""
    temperature: float | None = None
    top_p: float | None = None
    parallel_tool_calls: bool = False


class ModelConfigs(ConfigBaseModel):
    model_provider: ModelProviderConfig
    # for agent's model settings
    model_settings: ModelSettingsConfig = Field(default_factory=ModelSettingsConfig)
    # for basic model usage, e.g. `query_one` in tools / judger
    model_params: ModelParamsConfig = Field(default_factory=ModelParamsConfig)
