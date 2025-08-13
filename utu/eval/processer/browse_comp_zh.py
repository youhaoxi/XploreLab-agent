from ..data import EvaluationSample as Datapoint
from .browse_comp import BrowseCompProcesser
from .utils import MetricsUtils


class BrowseCompZHProcesser(BrowseCompProcesser):
    """Processer for BrowseCompZH evaluation."""

    name: str = "BrowseComp_ZH"

    def calculate_metrics(self, samples: list[Datapoint]) -> dict:
        """Calculate metrics from the judged data."""
        return {
            **MetricsUtils.calculate_overall_metrics(samples),
            **MetricsUtils.calculate_calibration(samples),
            **MetricsUtils.calculate_level_metrics(samples),
        }
