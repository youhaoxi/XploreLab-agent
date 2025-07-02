from typing import Callable, Literal

from pydantic import BaseModel


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
