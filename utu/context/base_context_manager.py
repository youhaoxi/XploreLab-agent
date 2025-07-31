import abc

from agents import TResponseInputItem
from agents.run import SingleStepResult

from ..utils import get_logger

logger = get_logger(__name__)


class BaseContextManager:
    def preprocess(self, input: str|list[TResponseInputItem]) -> str|list[TResponseInputItem]:
        if isinstance(input, str):
            return input
        processed_input = []
        for item in input:
            # skip reasoning, see chatcmpl_converter.Converter.items_to_messages()
            # agents.exceptions.UserError: Unhandled item type or structure: {'id': '__fake_id__', 'summary': [{'text': '...', 'type': 'summary_text'}], 'type': 'reasoning'}
            if item.get("type", None) == "reasoning":
                logger.info(f"Skip reasoning: {item}")
                continue
            processed_input.append(item)
        return processed_input

    @abc.abstractmethod
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        raise NotImplementedError

class DummyContextManager(BaseContextManager):
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        return single_step_result
