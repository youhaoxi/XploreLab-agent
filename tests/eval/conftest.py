import pytest

from utu.config import ConfigLoader, EvalConfig
from utu.eval.data import EvaluationSample
from utu.eval.data_processer import MixedProcesser
from utu.eval.evaluation import MixedEval

@pytest.fixture
def config() -> EvalConfig:
    return ConfigLoader.load_eval_config("default")

@pytest.fixture
def processer(config: EvalConfig) -> MixedProcesser:
    return MixedProcesser(config)

@pytest.fixture
async def data(processer: MixedProcesser) -> list[EvaluationSample]:
    return await processer.load_and_process("data/utu_test/agent_test.jsonl")

@pytest.fixture
def evaluator(config: EvalConfig) -> MixedEval:
    sources = ("GAIA", "BrowseComp", "BrowseComp_ZH", "Xbench")
    return MixedEval(sources, config)
