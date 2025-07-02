import re

from ..data import EvaluationSample
from .base import BaseLLMJudgeEval


class BrowseCompZHEval(BaseLLMJudgeEval):
    INSTRUCTIONS: str = """
如果你回复的问题需要借助外部资源，请根据你自身的知识储备给出具体答案，而不是拒答后让用户自行查询。

你的回复应遵循以下格式：
Explanation: {你对最终答案的解释}
Exact Answer: {你简洁的最终答案}
Confidence: {你对答案的置信度得分在 0% 到 100% 之间}
""".strip()
    JUDGE_TEMPLATE: str = """
根据以下精确且明确的[response]，判断以下对[question]的[correct_answer]是否正确。

[question]:  {question}

[response]:  {response}

您的判断必须符合以下指定的格式和标准：

extracted_final_answer: 从[response]中提取的最终准确答案。如果无法从答案中提取出准确的最终答案，则将提取的答案填写为"None"。

[correct_answer]: {correct_answer}

reasoning: 根据[correct_answer]解释提取的最终答案正确或错误的原因， 仅关注[correct_answer]和提取的最终答案之间是否存在有意义的差异。请勿评论问题的任何背景，请勿尝试解决问题，请勿争论任何与[correct_answer]不同的答案，仅关注答案是否匹配。

correct: 如果提取的最终答案与上面给出的[correct_answer]相符，或者在数值问题的误差范围内，则回答"yes"。否则，例如，如果存在任何不一致、歧义、不等同，或者提取的答案不正确，则回答"no"。

confidence: 从[response]中提取的置信度分数，介于0% 到100% 之间。如果没有可用的置信度分数，则填写100%。
""".strip()
    name: str = "BrowseComp_ZH"

    CONFIDENCE_BINS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
    
    def calculate_metrics(self, judged_data: list[EvaluationSample]) -> dict:
        """
        Calculate metrics from the judged data.
        """
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

        # 3. Calculate calibration statistics
        calibration = [{'samples':0, 'correct':0, 'conf_sum':0} for _ in self.CONFIDENCE_BINS]
        for record in judged_data:
            if record.judged_response == "invalid":
                continue
            confidence = record.confidence
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
        """
        Parse the judge response into a structured format.
        """
        pattern = re.compile(
            r"(?=.*?extracted_final_answer:\s*(?P<extracted_final_answer>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?reasoning:\s*(?P<reasoning>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?correct:\s*(?P<correct>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?confidence:\s*(?P<confidence>\d+)\s*%?(?=\n\s*\w+:|$))?",
            re.DOTALL
        )
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format")
        
        return {
            "extracted_final_answer": match.group("extracted_final_answer").strip() if match.group("extracted_final_answer") else None,
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else response.strip(),
            "correct": match.group("correct").strip().lower() == "yes" if match.group("correct") else False,
            "confidence": int(match.group("confidence")) if match.group("confidence") else None
        }

    def _calculate_calibration(self, stats: list[dict], total: int) -> float:
        """
        calculate calibration statistics
        """
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
        """
        Extract the exact answer from the response.
        """
        pattern = re.compile(r"Exact Answer:\s*(.*)")
        match = pattern.search(response)
        if not match:
            return ""
        return match.group(1).strip()
