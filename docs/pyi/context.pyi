import copy
from typing import Any, Literal
from dataclasses import dataclass

from agents import (
    TContext, TResponseInputItem, Agent, RunResult, AgentsException, ModelResponse,
    ItemHelpers, RunItem, RunContextWrapper
)
# from agents.run import AgentRunner
from agents._run_impl import (
    TraceCtxManager, 
    # SingleStepResult, 
    NextStepFinalOutput, NextStepHandoff, NextStepRunAgain, 
    RunImpl
)


""" 
@openai-agents 中的context/messages维护逻辑:
1. 对于一个输入, 运行 .run, 其包括多次的 .run_single_turn, 直到终止条件. 
2. 每个 single_turn 中, 输入 <original_input, generated_items>, 返回 SingleStepResult<original_input, model_response, pre_step_items, new_step_items, next_step>
3. **context management 实现思路**: 重写 _get_single_step_result_from_response, 增加后处理模块!
"""

class AgentRunner:
    async def run(self, starting_agent: Agent[TContext], input: str | list[TResponseInputItem], **kwargs) -> RunResult:
        with TraceCtxManager(...):
            current_turn = 0
            original_input: str | list[TResponseInputItem] = copy.deepcopy(input)
            generated_items: list[RunItem] = []
            model_responses: list[ModelResponse] = []
            try:
                while True:
                    if current_turn == 1: ...
                    else:
                        turn_result = await self._run_single_turn(
                            agent=current_agent,
                            original_input=original_input,
                            generated_items=generated_items,
                            hooks=hooks,
                            context_wrapper=context_wrapper,
                            tool_use_tracker=tool_use_tracker,  # TODO: tool_use_tracker?
                            # ...
                        )
                    model_responses.append(turn_result.model_response)
                    original_input = turn_result.original_input
                    generated_items = turn_result.generated_items
                    if isinstance(turn_result.next_step, NextStepFinalOutput):
                        return RunResult(
                            input=original_input,
                            new_items=generated_items,
                            raw_responses=model_responses,
                            final_output=turn_result.next_step.output,  
                            # ...
                        )
            except AgentsException as exc: ...

    @classmethod
    async def _run_single_turn(cls, *, agent, original_input, generated_items) -> SingleStepResult:
        # ... run agent_start_hooks

        input = ItemHelpers.input_to_new_input_list(original_input)
        input.extend([generated_item.to_input_item() for generated_item in generated_items])
        new_response = await cls._get_new_response(...)
        return await cls._get_single_step_result_from_response(...)

    @classmethod
    async def _get_single_step_result_from_response(cls,
    ) -> SingleStepResult:
        processed_response = RunImpl.process_model_response(
            agent=agent,
            all_tools=all_tools,
            response=new_response,
            output_schema=output_schema,
            handoffs=handoffs,
        )
        tool_use_tracker.add_tool_use(agent, processed_response.tools_used)
        return await RunImpl.execute_tools_and_side_effects(
            agent=agent,
            original_input=original_input,
            pre_step_items=pre_step_items,
            new_response=new_response,
            processed_response=processed_response,
            output_schema=output_schema,
            hooks=hooks,
            context_wrapper=context_wrapper,
            run_config=run_config,
        )

@dataclass
class SingleStepResult:
    original_input: str | list[TResponseInputItem]
    """The input items i.e. the items before run() was called. May be mutated by handoff input filters."""
    model_response: ModelResponse
    pre_step_items: list[RunItem]
    new_step_items: list[RunItem]
    next_step: NextStepHandoff | NextStepFinalOutput | NextStepRunAgain
    @property
    def generated_items(self) -> list[RunItem]:
        return self.pre_step_items + self.new_step_items



""" 
"""
# patch
class UTUAgentRunner(AgentRunner):
    @classmethod
    async def _get_single_step_result_from_response(context_wrapper: RunContextWrapper[TContext]) -> SingleStepResult:
        original_result = await super()._get_single_step_result_from_response(...)
        context_manager: ContextManager|None = context_wrapper.context.get("context_manager", None)
        return context_manager.process(original_result)
from agents.run import set_default_agent_runner
set_default_agent_runner(UTUAgentRunner)


class ContextManager:
    type: Literal["dummy", "summary"]
    config: Any

    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        """Postprocess the SingleStepResult<original_input, model_response, pre_step_items, new_step_items, next_step>"""
