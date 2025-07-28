
from dataclasses import dataclass
from agents import gen_trace_id

# from agents import RunResult
from ..config import AgentConfig, ConfigLoader
from .utils import NextTaskResult, SearchResult, AnalysisResult
from .ww_analyst import AnalysisAgent
from .ww_searcher_simple import SearcherAgent
from .ww_planner import PlannerAgent


@dataclass
class WWRunResult:
    final_output: str
    trajectory: list[dict]
    trace_id: str = ""


class WWAgent:
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
        trace_id = gen_trace_id()

        task_records: list[tuple[NextTaskResult, SearchResult]] = []
        trajectory: list[dict] = []  # for tracing
        analysis_result: AnalysisResult | None = None
        while True:
            next_task = await self.planner_agent.get_next_task(input, task_records[-1][1] if task_records else None, trace_id)
            trajectory.extend(next_task.trajectory)
            if next_task.is_finished: break

            if next_task.task.agent == "SearchAgent":
                result = await self.search_agent.research(next_task.task.task, trace_id=trace_id)
                task_records.append((next_task, result))
                trajectory.extend(result.trajectory)
            elif next_task.task.agent == "AnalysisAgent":
                analysis_result = await self.analysis_agent.analyze(task_records, trace_id=trace_id)
                trajectory.extend(analysis_result.trajectory)
            else:
                raise ValueError(f"Unknown agent name: {next_task.task.agent}")

        if analysis_result is None:
            analysis_result = await self.analysis_agent.analyze(task_records, trace_id=trace_id)
            trajectory.extend(analysis_result.trajectory)

        return WWRunResult(
            final_output=analysis_result.output,
            trajectory=trajectory,
            trace_id=trace_id,
        )
