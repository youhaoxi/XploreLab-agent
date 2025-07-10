""" WARNING: WIP! Not align with codebase

1. 概念层: 采用RL中的设置, agent <-> env
2. 实现层: 区分 build & runtime

相关问题:
1. agent tools v.s. env tools?
    前者是后者的函数签名
    逻辑上应该是环境提供工具列表 (注册), 并且在运行时完成该操作;
2. env v.s. tools?
    环境提供底层能力支持 (fs, shell, ...), 在其上运行工具 (类似 Linux core & CLI tools)

实现层面
- env v.s. Context@agents? 两者应该是一个东西
- @agents 中的依赖问题: Agent[model, tools, mcp_servers]
- 运行时变量: current_agent, input_items
- 封装 Runner: 提供 MCP management, tracing, hooks 等能力
"""

from typing import *
from pydantic import BaseModel, Field
from agents import *

from utu.config import AgentConfig


class Env:
    config: AgentConfig = None
    workdir: str = Field(description="working directory for the agent")
    context: Any = Field(description="context for openai-agents")

    async def get_state(self) -> str: ...
    async def get_tools(self) -> list[Tool]: ...


class RunnerMixin:
    """RunnerMixin
    - agent: 
    - env:
    """
    config: AgentConfig = None
    current_agent: Agent[TContext] = None
    input_items: list[TResponseInputItem] = []
    tracer: Trace = None
    env: Env = None
    _run_hooks: RunHooks = None

    # wrap apis in @openai-agents
    async def run(self, input: str | list[TResponseInputItem]) -> RunResult: ...
    def run_streamed(self, input: str | list[TResponseInputItem]) -> RunResultStreaming: ...
    # util apis
    async def chat(self, input: str) -> RunResult:
        """record history messages; print new items; update context"""
    async def chat_streamed(self, input: str):
        """streamed version"""

    def setup_tracer(self): ...
    def set_run_hooks(self, run_hooks: RunHooks): ...

class Agent(RunnerMixin):
    config: AgentConfig = None
    current_agent: Agent[TContext] = None
    input_items: list[TResponseInputItem] = []
    env: Env = None

    async def get_instructions(self) -> str | Callable: ...

    # lifecycle (can also use __aenter__ & __aexit__)
    async def build(self): ...
    async def cleanup(self): ...
