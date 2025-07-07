import re, string
import abc
import asyncio
from tqdm import tqdm
from openai import AsyncOpenAI

from ...config import EvalConfig
from ..data import EvaluationSample, EvaluationResult


DEFAULT_INSTRUCTIONS = "You are a helpful assistant."

class BaseEval:
    """
    Base class for automatic agent evaluation.
    """
    INSTRUCTIONS: str = DEFAULT_INSTRUCTIONS
    JUDGE_TEMPLATE: str = None

    concurrency_limit: int = None
    name: str = None

    def __init__(self, config: EvalConfig) -> None:
        """
        Initialize the evaluation with concurrency and thread size.
        """
        self.concurrency_limit = config.judge_concurrency

    async def eval(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        """
        Evaluate the agent on the predict data.
        """
        # 1. judge if each prediction is correct or not
        judged_data = await self.judge_with_asyncio(predict_data)
        return judged_data
    
    async def stat(self, judged_data: list[EvaluationSample]) -> EvaluationResult:
        # 2. calculate metrics based on judged results 
        metrics = self.calculate_metrics(judged_data)
        eval_result = EvaluationResult(
            benchmark=self.name,
            metrics=metrics
        )
        return eval_result

    async def judge_with_asyncio(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        async def judge_with_semaphore(item: EvaluationSample):
            async with semaphore:
                try:
                    return await self.judge_one(item)
                except Exception as e:
                    print(f">>>>>>>>>>>>>\nError judging sample '{item}': {e}\n<<<<<<<<<<<<<")
                    return None
        tasks = [judge_with_semaphore(item) for item in predict_data]
        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Judging"):
            result = await task
            if result is not None:
                results.append(result)
        return results

    @abc.abstractmethod
    async def judge(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        """
        Judge if the agent's predictions match ground truth.
        """
        pass

    @abc.abstractmethod
    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        """
        Judge a single sample.
        """
        pass

    @abc.abstractmethod
    def calculate_metrics(self, judged_data: list[EvaluationSample]) -> dict:
        """
        Calculate metrics from the judged data.
        """
        pass

    def get_instructions(self) -> str:
        # return the instructions for the agent
        return self.INSTRUCTIONS


DEFAULT_JUDGE_TEMPLATE = """
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


class BaseLLMJudgeEval(BaseEval):
    """
    Base class for evaluation with LLM judgement.
    """
    JUDGE_INSTRUCTIONS: str = DEFAULT_INSTRUCTIONS
    JUDGE_TEMPLATE: str = DEFAULT_JUDGE_TEMPLATE
    # judge model config
    judge_model: str = None
    judge_client: AsyncOpenAI = None

    max_tokens: int = None
    temperature: float = 0.5
    retries: int = 3

    name = "default"

    def __init__(self, config: EvalConfig) -> None:
        super().__init__(config)
        self.judge_model = config.judge_model
        self.judge_client = AsyncOpenAI(
            api_key=config.judge_api_key,
            base_url=config.judge_model_base_url,
        )
        self.max_tokens = config.judge_max_tokens
    
    async def judge(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        """
        Judge if the agent's predictions match ground truth.
        """
        # judge all data
        judged_data = []
        print(f"Judging {len(predict_data)} items with concurrency limit {self.concurrency_limit}...")
        tasks = [self.judge_one(data) for data in predict_data]
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            judged_data.append(result)
            print(f"Judged {i + 1}/{len(predict_data)} items...")
        return judged_data

    def calculate_metrics(self, judged_data: list[EvaluationSample]) -> dict:
        """
        Caculate metrics from the judged data.
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

        return {
            "Accuracy (%)": round(correct_count / total * 100, 4),
            "Details": {
                "correct": correct_count,
                "wrong": incorrect_count,
                "unknown": invalid_count,
                "total": total,
                "level_metrics": level_bin
            },
        }
    
    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        """
        Judge a single sample.
        """
        question = data.raw_question
        response = data.response
        correct_answer = data.correct_answer or "unknown"

        if correct_answer == "unknown":
            # if correct answer is unknown, we cannot judge
            data.update(judged_response="invalid",
                               correct=False)
            return data

        # if exact match, return directly(maybe extract exact answer from response first)
        if self._extract_exact_answer(response) == correct_answer:
            data.update(judged_response="Exact match",
                               correct=True)
            return data
        
        messages = self._get_judge_messages(
            question=question,
            response=response,
            correct_answer=correct_answer
        )
        content, parsed_content = "", {}
        for attempt in range(self.retries):
            try:
                result = await self.judge_client.chat.completions.create(
                    model=self.judge_model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                content = result.choices[0].message.content.strip()
                parsed_content = self._parse_judge_response(content)
                break
            except Exception as e:
                print(f"Error during judging: {e}, retrying {attempt + 1}/{self.retries}...")
                continue
        else:
            raise RuntimeError("Failed to judge after multiple retries.")

        data.judged_response = content
        # update the return data with parsed content
        data.update(**parsed_content)
        return data
    
    def _get_judge_messages(self, question: str, response: str, correct_answer: str) -> list:
        """
        Get the judge messages.
        """
        sp = self.JUDGE_INSTRUCTIONS
        input = self.JUDGE_TEMPLATE.format(
            question=question,
            response=response,
            correct_answer=correct_answer
        )
        return [
            {"role": "system", "content": sp},
            {"role": "user", "content": input}
        ]

    def _parse_judge_response(elf, response: str) -> dict:
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
            "extracted_final_answer": match.group("extracted_final_answer").strip(),
            "reasoning": match.group("reasoning").strip(),
            "correct":match.group("correct").strip().lower() == "yes",
            "confidence": int(match.group("confidence"))
        }

    def _extract_exact_answer(self, response: str) -> str:
        """
        Extract the exact answer from the response.
        """
        return response


class BaseMatchEval(BaseEval):
    """
    Base class for evaluation with exact match judgement.
    """
    async def judge(self, predict_data: list[EvaluationSample]) -> list[EvaluationSample]:
        """
        Judge if the agent's predictions match ground truth.
        """
        judged_data = []
        for data in predict_data:
            result_data = await self.judge_one(data)
            judged_data.append(result_data)

        return judged_data
    
    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        """
        Judge a single sample.
        """

        question = data.raw_question
        response = data.response
        correct_answer = data.correct_answer or "unknown"

        if_correct = False
        # if gt is a number
        if self._is_float(correct_answer):
            normalized_answer = self._normalize_number_str(str(response))
            if_correct = (normalized_answer == float(correct_answer))

        # if gt is a list
        elif any(char in correct_answer for char in [",", ";"]):
            # question with the fish: normalization removes punct

            gt_elems = self._split_string(correct_answer)
            ma_elems = self._split_string(response)

            # check length is the same
            if len(gt_elems) != len(ma_elems):
                data.update(correct=False)
                return data

            # compare each element as float or str
            comparisons = []
            for ma_elem, gt_elem in zip(ma_elems, gt_elems):
                if self._is_float(gt_elem):
                    normalized_ma_elem = self._normalize_number_str(ma_elem)
                    comparisons.append(normalized_ma_elem == float(gt_elem))
                else:
                    # we do not remove punct since comparisons can include punct
                    comparisons.append(
                        self._normalize_str(ma_elem, remove_punct=False)
                        == self._normalize_str(gt_elem, remove_punct=False)
                    )
            if_correct = all(comparisons)

        # if gt is a str
        else:
            if_correct = self._normalize_str(response) == self._normalize_str(correct_answer)

        data.update(correct=if_correct)
        return data

    def _is_float(self, s: str) -> bool:
        """
        Check if a string is a float.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False    
    
    def _normalize_number_str(self, s: str) -> float:
        """
        Normalize a number string to a float.
        """
        for char in ["$", "%", ","]:
           s = s.replace(char, "")
        try:
            return float(s)
        except ValueError:
            print(f"String {s} cannot be normalized to number str.")
            return float("inf")
    
    def _split_string(self, s: str, char_list: list[str] = [",", ";"]) -> list[str]:
        """
        Split a string by a list of characters.
        """
        pattern = f"[{''.join(char_list)}]"
        return re.split(pattern, s)
    
    def _normalize_str(self, s: str, remove_punct: bool = True) -> str:
        """
        Normalize a string by:
        - Removing all white spaces
        - Optionally removing punctuation (if remove_punct is True)
        - Converting to lowercase
        Parameters:
        - input_str: str, the string to normalize
        - remove_punct: bool, whether to remove punctuation (default: True)
        Returns:
        - str, the normalized string
        """
        # Remove all white spaces. Required e.g for seagull vs. sea gull
        no_spaces = re.sub(r"\s", "", s)

        # Remove punctuation, if specified.
        if remove_punct:
            translator = str.maketrans("", "", string.punctuation)
            return no_spaces.lower().translate(translator)
        else:
            return no_spaces.lower()
