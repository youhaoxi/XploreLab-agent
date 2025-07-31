import abc

from agents import TResponseInputItem
from agents.run import SingleStepResult

from ..utils import get_logger, ChatCompletionConverter

logger = get_logger(__name__)


class BaseContextManager:
    def preprocess(self, input: str|list[TResponseInputItem]) -> str|list[TResponseInputItem]:
        return ChatCompletionConverter.filter_items(input)

    @abc.abstractmethod
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        raise NotImplementedError

class DummyContextManager(BaseContextManager):
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        return single_step_result
