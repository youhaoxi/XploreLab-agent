from agents import Agent

from .simple_agent import SimpleAgent
from ..config import AgentConfig
from ..env import get_env
from ..utils import AgentsUtils


class SimpleEnvAgent(SimpleAgent):
    """SimpleAgent with environment
    """
    def __init__(self, config: AgentConfig|str, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

    async def build(self):
        self.env = await get_env("browser_docker", self.trace_id)
        await self.env.build()

        model = AgentsUtils.get_agents_model(**self.config.model.model_provider.model_dump())
        tools = await self.get_tools()
        tools += await self.env.get_tools()  # add env tools
        self.current_agent = Agent(
            name=self.config.agent.name,
            instructions=await self.build_instructions(),
            model=model,
            tools=tools,
            mcp_servers=self._mcp_servers
        )

    async def cleanup(self):
        await self.env.cleanup()
        await super().cleanup()

    async def build_instructions(self) -> str:
        return self.env.get_sp_prefix() + await super().build_instructions()
