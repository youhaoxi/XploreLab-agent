import re
import abc
import string

from ...config import EvalConfig
from ...utils import get_logger, SimplifiedAsyncOpenAI
from ..data import EvaluationSample, EvaluationResult
from .prompts import get_benchmark_templates
from .utils import MetricsUtils

logger = get_logger(__name__)


class BaseProcesser:
    """ Base class for processers in evaluation tasks. 
    
    Each processer implements the following evaluation phases:
      - load: load and process data (if necessary)
      - judge: judge the correctness of a batch of predictions
      - stat: get metrics. 
    """
    # prompt templates
    INSTRUCTION: str = None
    AUGMENTED_TEMPLATE: str = None
    JUDGE_TEMPLATE: str = None
    # concurrency limit
    name: str = None
    config: EvalConfig = None

    def __init__(self, config: EvalConfig) -> None:
        self._load_templates()
        self.config = config
    
    def preprocess_one(self, sample: EvaluationSample) -> EvaluationSample:
        """ Preprocess a single sample. """
        augmented_question = self._augment_question(sample.raw_question, sample.file_name)
        sample.update(
            augmented_question=augmented_question,
        )
        return sample

    @abc.abstractmethod
    async def stat(self, samples: list[EvaluationSample]) -> EvaluationResult:
        metrics = self.calculate_metrics(samples)
        eval_result = EvaluationResult(
            benchmark=self.name,
            metrics=metrics
        )
        return eval_result
    
    @abc.abstractmethod
    async def judge_one(self, sample: EvaluationSample) -> EvaluationSample:
        """ Judge a single sample. """
        pass

    @abc.abstractmethod
    def calculate_metrics(self, samples: list[EvaluationSample]) -> dict:
        """ Calculate metrics from the judged data. """
        pass

    def get_instructions(self) -> str:
        """ Get the instruction for the processer. """
        return self.INSTRUCTION if self.INSTRUCTION else ""
    
    def _load_templates(self):
        """ Load templates of current processer. """
        templates = get_benchmark_templates(self.name)
        self.INSTRUCTION = templates["system"]
        self.AUGMENTED_TEMPLATE = templates.get("augmented", None)
        self.JUDGE_TEMPLATE = templates.get("judge", None)
    
    def _augment_question(self, question: str, file_name: str = None) -> str:
        """ Augment the question with additional context or instructions. """
        input_prompt = self.AUGMENTED_TEMPLATE.format(question=question) if self.AUGMENTED_TEMPLATE else question
        file_prompt = self._get_file_prompt(file_name)
        return input_prompt + file_prompt
    
    def _get_file_prompt(self, file_name: str) -> str:
        """ Get file prompt if applicable. """
        return ""


class BaseLLMJudgeProcesser(BaseProcesser):
    """ Base class for processers that use LLM for judging. """
    name = "default"

    def __init__(self, config: EvalConfig) -> None:
        super().__init__(config)
        self.judge_client = SimplifiedAsyncOpenAI(**config.judge_model.model_provider.model_dump())

    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        """ Judge a single sample. """
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
            data.update(judged_response="Exact match", correct=True)
            return data
        
        messages = self._get_judge_messages(
            question=question,
            response=response,
            correct_answer=correct_answer
        )
        content = await self.judge_client.query_one(
            messages=messages,
            **self.config.judge_model.model_params.model_dump()
        )
        parsed_content = self._parse_judge_response(content)

        data.judged_response = content
        # update the return data with parsed content
        data.update(**parsed_content)
        return data

    def calculate_metrics(self, samples: list[EvaluationSample]) -> dict:
        """ Caculate metrics from the judged data. """
        return {
            **MetricsUtils.calculate_overall_metrics(samples),
            **MetricsUtils.calculate_level_metrics(samples),
        }

    def _get_judge_messages(self, question: str, response: str, correct_answer: str) -> list:
        """ Get the judge messages. """
        input = self.JUDGE_TEMPLATE.format(
            question=question,
            response=response,
            correct_answer=correct_answer
        )
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": input}
        ]

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
        # search for the pattern in the response
        match = pattern.search(response)
        if not match:
            raise ValueError("Invalid judge response format.")
        
        return {
            "extracted_final_answer": match.group("extracted_final_answer").strip() if match.group("extracted_final_answer") else "",
            "reasoning": match.group("reasoning").strip() if match.group("reasoning") else "",
            "correct": match.group("correct").strip().lower() == "yes" if match.group("correct") else False,
            "confidence": int(match.group("confidence")) if match.group("confidence") else None
        }

    def _extract_exact_answer(self, response: str) -> str:
        """ Extract the exact answer from the response. """
        return response.strip() if response else ""
    

class BaseMatchProcesser(BaseProcesser):
    """ Base class for processers that use match-based judging. """
    
    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        """ Judge a single sample. """
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
        """ Check if a string is a float. """
        try:
            float(s)
            return True
        except ValueError:
            return False    
    
    def _normalize_number_str(self, s: str) -> float:
        """ Normalize a number string to a float. """
        for char in ["$", "%", ","]:
           s = s.replace(char, "")
        try:
            return float(s)
        except ValueError:
            print(f"String {s} cannot be normalized to number str.")
            return float("inf")
    
    def _split_string(self, s: str, char_list: list[str] = [",", ";"]) -> list[str]:
        """ Split a string by a list of characters. """
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
