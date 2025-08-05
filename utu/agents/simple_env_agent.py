
from .simple_agent import SimpleAgent
from ..config import AgentConfig
from ..env import get_env


class UTUSimpleEnvAgent(SimpleAgent):
    """SimpleAgent with environment
    """
    def __init__(self, config: AgentConfig|str, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

    async def build(self):
        await super().build()
        self.env = await get_env("base", self.trace_id)

    async def cleanup(self):
        await self.env.cleanup()
        await super().cleanup()

    async def build_instructions(self) -> str:
        return self.env.get_sp_prefix() + await super().build_instructions()

    async def build(self):
        await super().build()

