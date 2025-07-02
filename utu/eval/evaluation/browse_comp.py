import re

from ..data import EvaluationSample
from .base import BaseLLMJudgeEval


class BrowseCompEval(BaseLLMJudgeEval):
    JUDGE_TEMPLATE: str = """
Judge whether the following [response] to [question] is correct or not based on the precise and unambiguous [correct_answer] below.

[question]: {question}

[response]: {response}

Your judgement must be in the format and criteria specified below:

extracted_final_answer: The final exact answer extracted from the [response]. Put the extracted answer as 'None' if there is no exact, final answer to extract from the response.

[correct_answer]: {correct_answer}

reasoning: Explain why the extracted_final_answer is correct or incorrect based on [correct_answer], focusing only on if there are meaningful differences between [correct_answer] and the extracted_final_answer. Do not comment on any background to the problem, do not attempt to solve the problem, do not argue for any answer different than [correct_answer], focus only on whether the answers match.

correct: Answer 'yes' if extracted_final_answer matches the [correct_answer] given above, or is within a small margin of error for numerical problems. Answer 'no' otherwise, i.e. if there if there is any inconsistency, ambiguity, non-equivalency, or if the extracted answer is incorrect.


confidence: The extracted confidence score between 0|\%| and 100|\%| from [response]. Put 100 if there is no confidence score available.
""".strip()
    name: str = "BrowseComp"
    
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
        
        # 2. Calculate confidence metrics
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
                "level_metrics": level_bin,
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
            raise ValueError("Invalid judge response format.")
        
        return {
            "extracted_final_answer": match.group("extracted_final_answer").strip() if match.group("extracted_final_answer") else None,
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else response.strip(),
            "correct": match.group("correct").strip().lower() == "yes" if match.group("correct") else False,
            "confidence": int(match.group("confidence")) if match.group("confidence") else None
        }

    def _extract_exact_answer(self, response: str) -> str:
        """
        Extract the exact answer from the response.
        """
        pattern = re.compile(r"Exact Answer:\s*(.*)")
        match = pattern.search(response)
        if not match:
            return ""
        return match.group(1).strip()
