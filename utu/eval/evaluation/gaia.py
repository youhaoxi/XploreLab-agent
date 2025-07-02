from ..data import EvaluationSample
from .base import BaseMatchEval


class GAIAEval(BaseMatchEval):
    name = "GAIA"

    def calculate_metrics(self, judged_data: list[EvaluationSample]) -> dict:
        # 1. calculate level metrics
        level_bin = {}
        invalid_count = 0
        for item in judged_data:
            level = item.level
            if level not in level_bin:
                level_bin[level] = {"correct": 0, "wrong": 0, "unknown": 0}
            if item.judged_response == "invalid":
                level_bin[level]["unknown"] += 1
                invalid_count += 1
                continue
            if item.correct:
                level_bin[level]["correct"] += 1
            else:
                level_bin[level]["wrong"] += 1
        # calculate overall metrics
        for level, counts in level_bin.items():
            total = counts["correct"] + counts["wrong"]
            if total > 0:
                counts["accuracy"] = round(counts["correct"] / total * 100, 4)
            else:
                counts["accuracy"] = 0.0
        # 2. calculate overall accuracy
        total = len(judged_data)
        correct_count = sum(item.correct for item in judged_data)
        incorrect_count = total - correct_count - invalid_count

        return {
            "Accuracy (%)": round(correct_count / total * 100, 4),
            "Details": {
                "correct": correct_count,
                "wrong": incorrect_count,
                "unknown": invalid_count,
                "total": total,
                "level_metrics": level_bin
            } 
        }
