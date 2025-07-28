import re

from ..data import EvaluationSample as Datapoint
from .base import BaseLLMJudgeProcesser


class BrowseCompZHProcesser(BaseLLMJudgeProcesser):
    """ Processer for BrowseCompZH evaluation. """
    name: str = "BrowseComp_ZH"

    CONFIDENCE_BINS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]

    def calculate_metrics(self, samples: list[Datapoint]) -> dict:
        """ Calculate metrics from the judged data. """
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

        # 3. Calculate calibration statistics
        calibration = [{'samples':0, 'correct':0, 'conf_sum':0} for _ in self.CONFIDENCE_BINS]
        for record in samples:
            if record.judged_response == "invalid":
                continue
            confidence = record.confidence or 0
            bin_idx = min(confidence // 20, len(self.CONFIDENCE_BINS) - 1)
            bin_stats = calibration[bin_idx]
            bin_stats['samples'] += 1
            bin_stats['conf_sum'] += confidence
            if record.get('correct', False):
                bin_stats['correct'] += 1
        calibration_error = round(self._calculate_calibration(calibration, total), 2)
        
        return {
            "Accuracy (%)": round(correct_count / total * 100, 4),
            "Calibration Error (%)": calibration_error,
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
            r"(?=.*?extracted_final_answer:\s*(?P<extracted_final_answer>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?reasoning:\s*(?P<reasoning>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?correct:\s*(?P<correct>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?confidence:\s*(?P<confidence>\d+)\s*%?(?=\n\s*\w+:|$))?",
            re.DOTALL
        )
        # remove the bold formatting
        response = response.replace("**", "")
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format")
        
        return {
            "extracted_final_answer": match.group("extracted_final_answer").strip() if match.group("extracted_final_answer") else "",
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else "",
            "correct": match.group("correct").strip().lower() == "yes" if match.group("correct") else False,
            "confidence": int(match.group("confidence")) if match.group("confidence") else None
        }

    def _calculate_calibration(self, stats: list[dict], total: int) -> float:
        """ calculate calibration statistics """
        error = 0.0
        for bin_stats in stats:
            samples = bin_stats['samples']
            if not samples:
                continue
            accuracy = bin_stats['correct'] / samples
            avg_conf = bin_stats['conf_sum'] / samples / 100  # convert to 0-1 decimal
            error += (samples / total) * abs(accuracy - avg_conf)
        return error * 100  # convert to percentage

    def _extract_exact_answer(self, response: str) -> str:
        """ Extract the exact answer from the response. """
        pattern = re.compile(r"Exact Answer:\s*(.*)")
        match = pattern.search(response)
        if not match or not match.group(1):
            return ""
        return match.group(1).strip()
