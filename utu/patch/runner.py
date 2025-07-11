
from agents.run import AgentRunner, AgentToolUseTracker, SingleStepResult
from agents import TContext, TResponseInputItem, Agent, Tool, ModelResponse, RunHooks, RunItem, RunContextWrapper, AgentOutputSchemaBase, RunConfig, Handoff

from ..context import BaseContextManager


class UTUAgentRunner(AgentRunner):
    @classmethod
    async def _get_single_step_result_from_response(
        cls,
        *,
        agent: Agent[TContext],
        all_tools: list[Tool],
        original_input: str | list[TResponseInputItem],
        pre_step_items: list[RunItem],
        new_response: ModelResponse,
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        hooks: RunHooks[TContext],
        context_wrapper: RunContextWrapper[TContext],
        run_config: RunConfig,
        tool_use_tracker: AgentToolUseTracker,
    ) -> SingleStepResult:
        original_result = await super()._get_single_step_result_from_response(
            agent=agent,
            original_input=original_input,
            pre_step_items=pre_step_items,
            new_response=new_response,
            output_schema=output_schema,
            all_tools=all_tools,
            handoffs=handoffs,
            hooks=hooks,
            context_wrapper=context_wrapper,
            run_config=run_config,
            tool_use_tracker=tool_use_tracker,
        )
        # FIXME: set context manage as a hook?
        context_manager: BaseContextManager|None = context_wrapper.context.get("context_manager", None)
        if context_manager:
            return context_manager.process(original_result)
        return original_result
