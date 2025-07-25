
from dataclasses import dataclass
from agents import gen_trace_id

# from agents import RunResult
from ..config import AgentConfig, ConfigLoader
from .utils import SearcherAgent, PlannerAgent, AnalysisAgent, NextTaskResult, SearchResult


@dataclass
class WWRunResult:
    final_output: str
    trajectory: list[dict]


class WWAgent:
    """ 简化版 agent, 仅提供 .build .run 接口 
    
    v1: 抽象出三个子agent
    """
    trace_id: str = None  # if for single run

    def __init__(self, config: AgentConfig|str):
        if isinstance(config, str):
            config = ConfigLoader.load_agent_config(config)
        self.config = config
        
        # init subagents
        self.search_agent = SearcherAgent(config)
        self.planner_agent = PlannerAgent(config)
        self.analysis_agent = AnalysisAgent(config)

    async def build(self):
        await self.search_agent.build()
        await self.planner_agent.build()
        await self.analysis_agent.build()

    async def run(self, input: str) -> WWRunResult:
        # setup
        self.trace_id = gen_trace_id()
        self.search_agent.agent.set_trace_id(self.trace_id)  # pass down trace_id

        task_records: list[tuple[NextTaskResult, SearchResult]] = []
        trajectory: list[dict] = []
        while True:
            next_task = await self.planner_agent.get_next_task(input, task_records[-1][1] if task_records else None)
            trajectory.extend(next_task.trajectory)
            if next_task.is_finished: break

            result = await self.search_agent.research(next_task.task)
            task_records.append((next_task, result))
            trajectory.extend(result.trajectory)
        
        analysis_result = await self.analysis_agent.analyze(task_records)
        trajectory.extend(analysis_result.trajectory)

        return WWRunResult(
            final_output=analysis_result.output,
            trajectory=trajectory,
        )
