import re

from ..data import EvaluationSample as Datapoint
from .base import BaseLLMJudgeProcesser
from .utils import MetricsUtils


class BrowseCompProcesser(BaseLLMJudgeProcesser):
    """Processer for BrowseComp evaluation."""

    name: str = "BrowseComp"

    def calculate_metrics(self, samples: list[Datapoint]) -> dict:
        """Calculate metrics for BrowseComp evaluation."""
        return {
            **MetricsUtils.calculate_overall_metrics(samples),
            **MetricsUtils.calculate_level_metrics(samples),
        }

    def _extract_exact_answer(self, response: str) -> str:
        """Extract the exact answer from the response."""
        pattern = re.compile(r"Exact Answer:\s*(.*)")
        match = pattern.search(response)
        if not match or not match.group(1):
            return ""
        return match.group(1).strip()
