from agents import RunContextWrapper, TContext, TResponseInputItem
from agents.run import SingleStepResult

from ..utils import ChatCompletionConverter, get_logger

logger = get_logger(__name__)


class BaseContextManager:
    def preprocess(
        self, input: str | list[TResponseInputItem], run_context: RunContextWrapper[TContext] = None
    ) -> str | list[TResponseInputItem]:
        return input

    def process(
        self, single_step_result: SingleStepResult, run_context: RunContextWrapper[TContext] = None
    ) -> SingleStepResult:
        return single_step_result


class DummyContextManager(BaseContextManager):
    def preprocess(
        self, input: str | list[TResponseInputItem], run_context: RunContextWrapper[TContext] = None
    ) -> str | list[TResponseInputItem]:
        # return ChatCompletionConverter.filter_items(input)
        return input

    # def process(self, single_step_result: SingleStepResult, run_context: RunContextWrapper[TContext]=None) -> SingleStepResult:
    #     return single_step_result
