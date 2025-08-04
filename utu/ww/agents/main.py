
from dataclasses import dataclass, asdict

from agents import gen_trace_id
from agents.tracing import function_span, trace, agent_span

from ...config import AgentConfig, ConfigLoader
from ...tracing import setup_tracing
from .utils import NextTaskResult, SearchResult, AnalysisResult
from .background_gen import ModuleGenBackground

# MODE = "simple | plan"
MODE = "plan"
if MODE == "simple":
    from .ww_analyst import DummyAnalysisAgent as AnalysisAgent
    from .ww_searcher import SimpleSearcherAgent as SearcherAgent
    from .ww_planner import DummyPlannerAgent as PlannerAgent
elif MODE == "plan":
    from .ww_analyst import AnalysisAgent
    # from .ww_searcher import SearcherAgent
    from .ww_searcher import SimpleSearcherAgent as SearcherAgent
    from ..planner import PlannerAgent
else:
    raise ValueError(f"Unknown mode: {MODE}")


@dataclass
class WWRunResult:
    final_output: str
    trajectory: list[dict]  # TODO: add handoff info
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
        self.background_gen = ModuleGenBackground()

    async def build(self):
        await self.search_agent.build()
        await self.planner_agent.build()
        await self.analysis_agent.build()

    async def run(self, input: str) -> WWRunResult:
        # setup
        setup_tracing()
        trace_id = gen_trace_id()

        # task_records: list[tuple[NextTaskResult, SearchResult]] = []
        trajectory: list[dict] = []  # for tracing
        analysis_result: AnalysisResult | None = None

        # FIXME: error_tracing
        with trace(workflow_name="ww_agent", trace_id=trace_id):
            # input_background = await self.background_gen.generate_background_info(input)
            # aug_input = f"{input}\n\nBackgrounds maybe helpful: {input_background['background']}"
            
            # aug_input = input
            # while True:
            #     next_task = await self.plan(aug_input, trace_id=trace_id)
            #     trajectory.extend(next_task.trajectory)
            #     if next_task.is_finished: break

            # MODE 2: plan & exec
            task_records: list[SearchResult] = []
            plan = await self.plan(input, trace_id=trace_id)
            trajectory.extend(plan.trajectory)
            for task in plan.todo:
                if task.agent_name == "SearchAgent":
                    result = await self.search_agent.research(task.task, trace_id=trace_id)
                    task_records.append(result)
                    trajectory.extend(result.trajectory)
                elif task.agent_name == "AnalysisAgent":
                    analysis_result = await self.analyze(input, task_records, trace_id=trace_id)
                    trajectory.extend(analysis_result.trajectory)
                else:
                    raise ValueError(f"Unknown agent name: {task.agent_name}")

            if analysis_result is None:
                analysis_result = await self.analyze(input, task_records, trace_id=trace_id)
                trajectory.extend(analysis_result.trajectory)

        return WWRunResult(
            final_output=analysis_result.output,
            trajectory=trajectory,
            trace_id=trace_id,
        )

    async def plan(self, input: str, prev_task: str = None, prev_subtask_result: str = None, trace_id: str = None) -> NextTaskResult:
        with function_span("planner") as span_planner:
            next_task = await self.planner_agent.get_next_task(input, prev_task, prev_subtask_result, trace_id)
            span_planner.span_data.input = str({"input": input, "prev_subtask_result": prev_subtask_result})
            span_planner.span_data.output = asdict(next_task)
        return next_task

    async def analyze(self, input: str, task_records: list[SearchResult], trace_id: str = None) -> AnalysisResult:
        with function_span("analysis") as span_fn:
            analysis_result = await self.analysis_agent.analyze(input, task_records, trace_id=trace_id)
            span_fn.span_data.input = str({"input": input, "task_records": task_records})
            span_fn.span_data.output = asdict(analysis_result)
        return analysis_result
