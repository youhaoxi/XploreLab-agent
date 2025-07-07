import re

from ..data import EvaluationSample
from .base import BaseLLMJudgeEval


class XBenchEval(BaseLLMJudgeEval):
    JUDGE_TEMPLATE: str = """
你是一个通用人工智能助手。根据下面给出的[正确答案], 判断以下对[原问题]的[回答]的回答是否正确。

[原问题]: {question}

[正确答案]: {correct_answer}

[回答]:{response}

你的判断必须按照以下格式和标准进行:

最终答案: 从[回答]中提取出的最终准确答案。如果[回答]中没有明确的最终答案, 则填写'无'。

解释: 根据[正确]解释为什么[最终答案]是正确的或错误的。只关注[最终答案]与[正确答案]之间是否存在实质性差异, 不要评论题目的背景, 不要尝试重新解题, 不要为任何不同于[正确答案]的答案辩护, 只专注于判断答案是否一致。

结论: 如果[最终答案]与上方给出的[正确答案]一致, 或者在数值题目中处于可接受的微小误差范围内, 则填写'正确'; 否则（即存在任何不一致、歧义、不等价或提取出的答案错误的情况）填写'错误'。
""".strip()
    name: str = "XBench"
    
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
        
        # 3. Calculate confidence metrics
        for item in judged_data:
            if item.confidence is None:
                item.confidence = 100 if item.judged_response == "Exact match" else 0
        confidence_scores = [item.confidence for item in judged_data if item.judged_response != "invalid"]
        
        return {
            "Accuracy (%)": round(correct_count / total * 100, 2),
            "Average Confidence (%)": round(sum(confidence_scores) / total, 2),
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
            r"(?=.*?最终答案:\s*(?P<extracted_final_answer>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?解释:\s*(?P<reasoning>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?结论:\s*(?P<correct>.*?)(?=\n\s*\w+:|$))?",
            re.DOTALL
        )
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format.")
        
        return {
            "extracted_final_answer": match.group("extracted_final_answer").strip() if match.group("extracted_final_answer") else None,
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else response.strip(),
            "correct": match.group("correct").strip() == "正确" if match.group("correct") else False,
        }
    
    def _extract_exact_answer(self, response: str) -> str:
        """
        Earse the exact answer from the response.
        """
        pattern = re.compile(r"最终答案:\s*(.*)")
        match = pattern.search(response)
        if not match:
            return ""
        return match.group(1).strip()
