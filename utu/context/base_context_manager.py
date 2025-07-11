import abc
import logging

from agents.run import SingleStepResult

logger = logging.getLogger(__name__)


class BaseContextManager(abc.ABC):
    @abc.abstractmethod
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        raise NotImplementedError

class DummyContextManager(BaseContextManager):
    def process(self, single_step_result: SingleStepResult) -> SingleStepResult:
        logger.info("DummyContextManager: process")
        return single_step_result
