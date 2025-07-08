from ...config import EvalConfig
from ..data import EvaluationSample, EvaluationResult
from .base import BaseEval
from . import EVAL_FACTORY


class MixedEval:
    """
    Class to evaluate data from different benchmarks using a unified interface.  
    """
    _evaluators: dict[str, BaseEval]  # cache evaluators for different benchmarks

    def __init__(self, sources: set[str], config: EvalConfig):
        # TODO: remove sources
        self._evaluators = {}
        for source in sources:
            if source not in self._evaluators:
                self._evaluators[source] = EVAL_FACTORY.get(source, config or EvalConfig())
    
    async def eval(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        """
        Evaluate the predictions.
        """
        data_by_benchmark = self._group_data_by_benchmark(predict_data)
        # evaluate each benchmark
        overall_judged_data = []
        for benchmark, data in data_by_benchmark.items():
            evaluator = self._evaluators.get(benchmark)
            judged_data = await evaluator.eval(data)
            overall_judged_data.extend(judged_data)
        return overall_judged_data

    async def stat(self, judged_data: list[EvaluationSample]) -> EvaluationResult:
        # TODO: wrap the data like @verl / @torch
        # TODO: unify mixed & single mode
        # TODO: log to wandb
        data_by_benchmark = self._group_data_by_benchmark(judged_data)
        overall_results = []
        for benchmark, data in data_by_benchmark.items():
            evaluator = self._evaluators.get(benchmark)
            result = await evaluator.stat(data)
            result.update(benchmark=benchmark)
            overall_results.append(result)
        
        overall_metrics = self._calculate_overall_metrics(overall_results, len(judged_data))
        eval_result = EvaluationResult(
            benchmark="mixed",
            metrics=overall_metrics
        )
        return eval_result
    
    def _group_data_by_benchmark(self, predict_data: list[EvaluationSample]) -> dict[str, list[EvaluationSample]]:
        # group data by benchmark
        data_by_benchmark = {}
        for data in predict_data:
            benchmark = data.source
            if benchmark not in data_by_benchmark:
                data_by_benchmark[benchmark] = []
            
            data_by_benchmark[benchmark].append(data)
        return data_by_benchmark

    def get_instructions(self) -> dict[str, str]:
        """
        Get the instructions for each benchmark.
        """
        benchmark_instructions = {benchmark: evaluator.get_instructions() for benchmark, evaluator in self._evaluators.items()}
        return benchmark_instructions

    def _calculate_overall_metrics(self, results: list[EvaluationResult], total: int) -> dict:
        """
        Calculate overall metrics from the results of different benchmarks.
        """
        # 1. calculate level metrics
        level_bin = {}
        for result in results:
            for level, metric_info in result.metrics.get("Details", {}).get("level_metrics", {}).items():
                if level not in level_bin:
                    level_bin[level] = {"correct": 0, "wrong": 0, "unknown": 0}
                level_bin[level]["correct"] += metric_info.get("correct", 0)
                level_bin[level]["wrong"] += metric_info.get("wrong", 0)
                level_bin[level]["unknown"] += metric_info.get("unknown", 0)
        total, total_valid = 0, 0
        for level, counts in level_bin.items():
            level_total_valid = counts["correct"] + counts["wrong"]
            level_total = level_total_valid + counts["unknown"]
            total += level_total
            total_valid += level_total_valid
            if level_total_valid > 0:
                counts["accuracy"] = round(counts["correct"] / level_total_valid * 100, 4)
            else:
                counts["accuracy"] = 0.0
        # 2. calculate overall accuracy
        correct_count = sum(result.metrics.get("Details", {}).get("correct", 0) for result in results)
        incorrect_count = total_valid - correct_count
        overall_metrics = {
            "Accuracy (%)": round(correct_count / total * 100, 4),
            "Details": {
                "correct": correct_count,
                "wrong": incorrect_count,
                "unknown": total - total_valid,
                "total": total,
                "level_metrics": level_bin,
                "benchmarks": [result.as_dict() for result in results],
            }
        }
        return overall_metrics
    
