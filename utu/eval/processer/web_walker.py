import re

from ..data import EvaluationSample as Datapoint
from .base import BaseLLMJudgeProcesser


class WebWalkerProcesser(BaseLLMJudgeProcesser):
    """ Processer for WebWalker evaluation. """
    name: str = "WebWalker"

    def calculate_metrics(self, samples: list[Datapoint]) -> dict:
        """ Calculate metrics from the judged data. """
        """
        Calculate metrics from the judged data.
        """
        # 1. calculate level metrics
        level_bin = {}
        invalid_count = 0
        for item in samples:
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
        total = len(samples)
        correct_count = sum(item.correct for item in samples)
        incorrect_count = total - correct_count - invalid_count
        
        return {
            "Accuracy (%)": round(correct_count / total * 100, 2),
            "Details": {
                "correct": correct_count,
                "wrong": incorrect_count,
                "unknown": invalid_count,
                "total": total,
                "level_metrics": level_bin
            } 
        }
    
    def _parse_judge_response(self, response: str) -> dict:
        """ Parse the judge response into a structured format. """
        pattern = re.compile(
            r"(?=.*?EXPLANATION:\s*(?P<reasoning>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?GRADE:\s*(?P<correct>.*?)(?=\n\s*\w+:|$))?",
            re.DOTALL
        )
        # remove the bold formatting
        response = response.replace("**", "")
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format.")
        
        return {
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else "",
            "correct": match.group("correct").strip() == "CORRECT" if match.group("correct") else False,
        }

    def _extract_exact_answer(self, response: str) -> str:
        """ Extract the exact answer from the response. """
        # not specified in the template, so we return the original response
        return response.strip() if response else ""
