""" 
Simple agent with built-in tools
- [ ] MCP
"""
from typing import Callable
from agents import Agent, Tool

from .base import UTUAgentBase
from ..utils import AgentsUtils
from ..tools import load_toolkit


class UTUSimpleAgent(UTUAgentBase):
    def __init__(
        self,
        config_name: str = "simple",
        name: str = None,
        instructions: str = None,
        *args, **kwargs
    ):
        super().__init__(config_name, *args, **kwargs)
        # override config
        if name: self.config.agent.name = name
        if instructions: self.config.agent.instructions = instructions

    async def build(self):
        """ Build the agent """
        model = AgentsUtils.get_agents_model(**self.config.model.model_dump())
        self._current_agent = Agent(
            name=self.name,
            instructions=await self.build_instructions(),
            model=model,
            tools=await self.load_tools(),
        )

    async def load_tools(self) -> list[Tool]:
        """ Load tools from config. You can override this method to load tools from other sources. """
        tools = []
        for toolkit_config in self.config.toolkits:
            toolkit = load_toolkit(toolkit_config)
            tools.extend(await toolkit.get_tools_in_agents())
        return tools

    async def build_instructions(self) -> str | Callable:
        """ Build instructions from config. You can override this method to build customized instructions. """
        return self.config.agent.instructions
