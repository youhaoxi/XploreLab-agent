"""
- [x] feat: support multi-turn chat
- [ ] feat: add reporter
    additional instructions for the last agent! (as the reporter)
- [ ] feat: replan
- [ ] add name & description for all agent types
"""

import asyncio

from agents import trace

from ..config import AgentConfig, ConfigLoader
from ..utils import AgentsUtils, FileUtils, get_logger
from .common import QueueCompleteSentinel
from .orchestrator.chain import Orchestrator, Recorder, Task
from .simple_agent import SimpleAgent

logger = get_logger(__name__)
PROMPTS = FileUtils.load_prompts("agents/orchestrator/chain.yaml")


class OrchestratorAgent:
    def __init__(self, config: AgentConfig):
        self._handle_config(config)

        self.orchestrator = Orchestrator(self.config)
        self.workers = self._setup_workers()

    @property
    def name(self) -> str:
        return self.config.orchestrator_config.get("name", "BaseOrchestratorAgent")

    def _handle_config(self, config: AgentConfig) -> None:
        add_chitchat_subagent = config.orchestrator_config.get("add_chitchat_subagent", True)
        if add_chitchat_subagent:
            config.orchestrator_workers["ChitchatAgent"] = ConfigLoader.load_agent_config("simple/chitchat")
            config.orchestrator_workers_info.append(
                {
                    "name": "ChitchatAgent",
                    "description": "Engages in light, informal conversations and handles straightforward queries. Can optionally invoke search or Python tools for simple fact checks or quick calculations.",  # noqa: E501
                }
            )
        self.config = config

    def _setup_workers(self) -> dict[str, SimpleAgent]:
        # TODO: manipulate SP of agents when as workers
        workers = {}
        for name, config in self.config.orchestrator_workers.items():
            assert config.type == "simple", f"Only support SimpleAgent as worker in orchestra agent, get {config}"
            workers[name] = SimpleAgent(config=config)
        return workers

    async def run(self, input: str, history: Recorder = None) -> Recorder:
        recorder = self.run_streamed(input, history)
        async for _ in recorder.stream_events():
            pass
        return recorder

    def run_streamed(self, input: str, history: Recorder = None) -> Recorder:
        if history:
            recorder = history.new(input=input)
        else:
            recorder = Recorder(input=input)
        recorder._run_impl_task = asyncio.create_task(self._start_streaming(recorder))
        return recorder

    async def _start_streaming(self, recorder: Recorder):
        with trace(workflow_name=self.name) as tracer:
            recorder.trace_id = tracer.trace_id  # record trace_id
            try:
                await self.orchestrator.create_plan(recorder)
                while True:
                    task = await self.orchestrator.get_next_task(recorder)
                    if not task:
                        recorder.final_output = recorder.tasks[-1].result
                        break
                    await self._run_task(recorder, task)
            except Exception as e:
                logger.error(f"Error processing task: {str(e)}")
                recorder._event_queue.put_nowait(QueueCompleteSentinel())
                recorder._is_complete = True
                raise e
            finally:
                recorder._event_queue.put_nowait(QueueCompleteSentinel())
                recorder._is_complete = True

    async def _run_task(self, recorder: Recorder, task: Task):
        worker = self.workers[task.agent_name]
        await worker.build()
        # build context for task
        task_with_context = FileUtils.get_jinja_template_str(PROMPTS["worker"]).render(
            problem=recorder.input,
            plan=recorder.get_plan_str(),
            trajectory=recorder.get_trajectory_str(),
            task=task.task,
        )
        # run the task
        result = worker.run_streamed(task_with_context)
        async for event in result.stream_events():
            recorder._event_queue.put_nowait(event)
        # set result & record trajectory
        task.result = result.final_output
        recorder.trajectories.append(AgentsUtils.get_trajectory_from_agent_result(result))
