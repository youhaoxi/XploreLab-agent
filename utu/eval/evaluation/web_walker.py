import re

from ..data import EvaluationSample
from .base import BaseLLMJudgeEval


class WebWalkerEval(BaseLLMJudgeEval):
    JUDGE_TEMPLATE: str = """
You are a teacher grading a quiz.
You are given a question, the context the question is about, and the student's answer. You are asked to score the student's answer as either CORRECT or INCORRECT, based on the context.
Write out in a step by step manner your reasoning to be sure that your conclusion is correct. Avoid simply stating the correct answer at the outset.

Example Format:
QUESTION: question here
CONTEXT: context the question is about here
STUDENT ANSWER: student's answer here
EXPLANATION: step by step reasoning here
GRADE: CORRECT or INCORRECT here

Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer, as long as it does not contain any conflicting statements. Begin! 

QUESTION: {query}
CONTEXT: {context}
STUDENT ANSWER: {result}
EXPLANATION:
""".strip()
    name: str = "WebWalker"

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
    
    def _parse_judge_response(self, response):
        """
        Parse the judge response into a structured format.
        """
        pattern = re.compile(
            r"(?=.*?EXPLANATION:\s*(?P<reasoning>.*?)(?=\n\s*\w+:|$))?"
            r"(?=.*?GRADE:\s*(?P<correct>.*?)(?=\n\s*\w+:|$))?",
            re.DOTALL
        )
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format.")
        
        return {
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else response.strip(),
            "correct": match.group("correct").strip() == "CORRECT" if match.group("correct") else False,
        }
    
    def _extract_exact_answer(self, response):
        """
        Extract the exact answer from the response.
        """
        # not specified in the template, so we return the original response
        return response.strip()
