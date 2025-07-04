
from agents import (
    Agent, Runner, RunConfig, 
    RunResult, RunResultStreaming, RunHooks,
    TResponseInputItem
)

from ..utils import AgentsUtils
from ..config import ConfigLoader, AgentConfig
from .context import UTUContext


class UTUAgentBase:
    config: AgentConfig = None
    context: UTUContext = None
    
    _run_hooks: RunHooks = None

    @property
    def name(self) -> str:
        return self.config.agent.name

    def __init__(self, config: AgentConfig|str):
        self._load_config(config)
        self._build_context()

    def _load_config(self, config: str|AgentConfig):
        if isinstance(config, str):
            config = ConfigLoader.load_agent_config(config)
        self.config = config
    def _build_context(self):
        self.context = UTUContext(config=self.config)

    def _get_run_config(self) -> RunConfig:
        return RunConfig(
            workflow_name=self.name,
        )

    def set_agent(self, agent: Agent):
        """ Set the current agent """
        self.context.current_agent = agent

    def set_run_hooks(self, run_hooks: RunHooks):
        self._run_hooks = run_hooks

    # wrap `Runner` apis in @openai-agents
    async def run(self, input: str | list[TResponseInputItem]) -> RunResult:
        # TODO: setup other runner options as @property
        return await Runner.run(
            self.context.current_agent, 
            input, 
            # TODO: max_turns
            context=self.context,
            run_config=self._get_run_config(), 
            hooks=self._run_hooks
        )

    def run_streamed(self, input: str | list[TResponseInputItem]) -> RunResultStreaming:
        return Runner.run_streamed(
            self.context.current_agent, 
            input, 
            context=self.context,
            run_config=self._get_run_config(), 
            hooks=self._run_hooks
        )

    # util apis
    async def chat(self, input: str):
        # TODO: support multi-modal input -- `def add_input(...)`
        # TODO: set "session-level" tracing for multi-turn chat
        self.context.input_items.append({"content": input, "role": "user"})
        run_result = await self.run(self.context.input_items)
        AgentsUtils.print_new_items(run_result.new_items)
        self.context.input_items = run_result.to_input_list()
        self.context.current_agent = run_result.last_agent
    
    async def chat_streamed(self, input: str):
        self.context.input_items.append({"content": input, "role": "user"})
        run_result_streaming = self.run_streamed(self.context.input_items)
        await AgentsUtils.print_stream_events(run_result_streaming.stream_events())
        self.context.input_items = run_result_streaming.to_input_list()
        self.context.current_agent = run_result_streaming.last_agent
