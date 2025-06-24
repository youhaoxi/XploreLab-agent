from agents import (
    Agent, Runner, RunConfig, RunResult, RunResultStreaming, 
    TResponseInputItem
)

from ..utils import AgentsUtils
from ..config import load_config_by_name, Config


class UTUAgentBase:
    config: Config = None
    
    _current_agent: Agent = None
    _input_items: list[TResponseInputItem] = []

    @property
    def name(self):
        return self.config.agent.name

    def __init__(
        self,
        config_name: str = "default",
    ):
        self._load_config(config_name)

    def _load_config(self, config_name: str):
        self.config = load_config_by_name(config_name)

    def _get_run_config(self) -> RunConfig:
        return RunConfig(
            workflow_name=self.name,
        )

    def set_agent(self, agent: Agent):
        """ Set the current agent """
        self._current_agent = agent

    # wrap `Runner` apis in @openai-agents
    async def run(self, input: str | list[TResponseInputItem]) -> RunResult:
        # TODO: setup other runner options as @property
        return await Runner.run(self._current_agent, input, run_config=self._get_run_config())

    def run_streamed(self, input: str | list[TResponseInputItem]) -> RunResultStreaming:
        return Runner.run_streamed(self._current_agent, input, run_config=self._get_run_config())

    # util apis
    async def chat(self, input: str):
        # TODO: support multi-modal input -- `def add_input(...)`
        self._input_items.append({"content": input, "role": "user"})
        run_result = await self.run(self._input_items)
        AgentsUtils.print_new_items(run_result.new_items)
        self._input_items = run_result.to_input_list()
        self._current_agent = run_result.last_agent
    
    async def chat_streamed(self, input: str):
        self._input_items.append({"content": input, "role": "user"})
        run_result_streaming = self.run_streamed(self._input_items)
        await AgentsUtils.print_stream_events(run_result_streaming.stream_events())
        self._input_items = run_result_streaming.to_input_list()
        self._current_agent = run_result_streaming.last_agent
