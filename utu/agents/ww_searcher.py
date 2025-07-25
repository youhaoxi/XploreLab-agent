from .utils import Base, SearchResult
from ..config import AgentConfig
from .simple_agent import SimpleAgent
from ..eval.common import get_trajectory_from_agent_result


class SearcherAgent(Base):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.agent = SimpleAgent(config)  # v0

    async def build(self):
        await self.agent.build()

    async def research(self, subtask: str) -> SearchResult:
        """search webpages for a specific subtask, return a report """
        run_result = await self.agent.run(subtask)
        return SearchResult(
            output=run_result.final_output,
            trajectory=get_trajectory_from_agent_result(run_result),
        )
