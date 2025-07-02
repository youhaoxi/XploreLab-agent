from typing import Callable, Literal, Optional

from pydantic import BaseModel, Field

DEFAULT_INSTRUCTIONS = "You are a helpful assistant."

class ModelConfig(BaseModel):
    api_key: str
    base_url: str
    model: str

class ProfileConfig(BaseModel):
    name: Optional[str] = "default"
    instructions: Optional[str | Callable] = DEFAULT_INSTRUCTIONS

class ToolkitConfig(BaseModel):
    mode: Literal["builtin", "mcp"] = "builtin"
    name: str
    activated_tools: list[str] | None = None
    config: dict | None = None

class AgentConfig(BaseModel):
    model: ModelConfig
    agent: ProfileConfig = Field(default_factory=ProfileConfig)
    toolkits: dict[str, ToolkitConfig] = Field(default_factory=dict)
    
