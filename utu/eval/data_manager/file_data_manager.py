
import pathlib
from typing import List

from ...utils import DIR_ROOT
from ...config import EvalConfig
from ..common import EvaluationSample
from ..data_processer import DATA_PROCESSER_FACTORY, MixedProcesser, BUILTIN_BENCHMARKS

DIR_EVAL_OUT = DIR_ROOT / "utu" / "eval" / "output"
pathlib.Path(DIR_EVAL_OUT).mkdir(parents=True, exist_ok=True)


class FileDataManager:
    def __init__(self, config: EvalConfig):
        self.config = config

    def _parse_config(self):
        config = self.config
        if config.type == "single":
            if config.dataset in BUILTIN_BENCHMARKS:
                # load builtin benchmark
                dataset_info = BUILTIN_BENCHMARKS[config.dataset]
                data_path = str(dataset_info["data_path"])
                processer_name = dataset_info["processer"]
                evaluator_name = dataset_info["evaluator"]
            else:
                data_path = config.dataset
                processer_name = "default"
                evaluator_name = "default"
        else:
            # mixed dataset
            data_path = config.dataset
            processer_name = "mixed"
            evaluator_name = "mixed"
        # if assign a specific evalution method, use the corresponding processer and evaluator
        if config.eval_method:
            processer_name = config.eval_method
            evaluator_name = config.eval_method
        return data_path, processer_name, evaluator_name

    async def load_dataset(self) -> List[EvaluationSample]:
        """Load the raw dataset."""
        data_path, processer_name, _ = self._parse_config()
        if processer_name == "mixed":
            processer = MixedProcesser(self.config)
        else:
            processer = DATA_PROCESSER_FACTORY.get(processer_name, self.config)
        return await processer.load_and_process(data_path)
