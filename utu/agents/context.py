from contextlib import AsyncExitStack
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from agents import TResponseInputItem, Agent
from agents.mcp import MCPServer

from ..config import Config


class UTUContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # tools
    config: Config
    current_agent: Any = None
    input_items: list[TResponseInputItem] = Field(default_factory=list)
    exit_stack: AsyncExitStack = Field(default_factory=AsyncExitStack)
    dynamic_mcp_servers: list[MCPServer] = Field(default_factory=list)

UTUContext.model_rebuild()