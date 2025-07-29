import abc

from agents.run import SingleStepResult

from ..utils import get_logger

logger = get_logger(__name__)


class BaseContextManager(abc.ABC):
    @abc.abstractmethod
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        raise NotImplementedError

class DummyContextManager(BaseContextManager):
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        return single_step_result
