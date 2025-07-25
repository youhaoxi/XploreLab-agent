import json

from dataclasses import dataclass
from agents import gen_trace_id

# from agents import RunResult
from .simple_agent import SimpleAgent
from ..config import AgentConfig, ConfigLoader
from ..eval.common import get_trajectory_from_agent_result

@dataclass
class WWRunResult:
    final_output: str
    trajectory: str


class WWAgent:
    """ 简化版 agent, 仅提供 .build .run 接口 
    
    v0: 复用 SimpleAgent, 仅用于串通流程
    """
    trace_id: str = None  # if for single run

    def __init__(self, config: AgentConfig|str):
        if isinstance(config, str):
            config = ConfigLoader.load_agent_config(config)
        self.config = config
        self.agent = SimpleAgent(config)  # v0

    async def build(self):
        await self.agent.build()

    async def run(self, input: str) -> WWRunResult:
        self.trace_id = gen_trace_id()
        result = await self.agent.run(input)
        return WWRunResult(
            final_output=result.final_output,
            trajectory=json.dumps(get_trajectory_from_agent_result(result), ensure_ascii=False),
        )
