import os
import abc
import json
import aiofiles
import pathlib

from utu.eval import EvaluationSample
from utu.config import EvalConfig


class BaseProcesser:
    """
    Base class for data pre-processing in evaluation tasks.
    """
    AUGMENTED_TEMPLATE: str = None
    # data fileds
    question_filed: str = None
    gt_filed: str = None
    name: str = None

    def __init__(self,
                 config: EvalConfig) -> None:
        self.question_filed = config.question_field
        self.gt_filed = config.gt_field

    async def load_and_process(self, data_path: str) -> list[EvaluationSample]:
        """
        Load and process data from the specified path.
        """
        data_dict = await self._load_data(data_path)
        samples = []
        for item in data_dict:
            sample = self.process_one(item)
            samples.append(sample)
        return samples
    
    def process_one(self, item: dict) -> EvaluationSample:
        """
        Process a single item into an EvaluationSample.
        """
        question = item.get(self.question_filed, "")
        gt = item.get(self.gt_filed, "")
        file_name = item.get("file_name", None)  # for GAIA
        sample = EvaluationSample(
                source=item.get("source", self.name),
                raw_question=question,
                level=item.get("level", 0),  # if applicable
                augmented_question=self._augment_question(question, file_name),
                correct_answer=gt,
                file_name=file_name
            )
        return sample

    async def _load_data(self, data_path: str) -> list[dict]:
        """
        Load data from different formats.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file {data_path} does not exist.")
        if data_path.endswith('.jsonl'):
            async with aiofiles.open(data_path, 'r', encoding='utf-8') as f:
                return [json.loads(line.strip()) async for line in f]
        elif data_path.endswith('.json'):
            async with aiofiles.open(data_path, 'r', encoding='utf-8') as f:
                return json.loads(await f.read())
        else:
            raise ValueError("Unsupported file format. Please use a JSONL or JSON file.")
        
    def _augment_question(self, question: str, file_name: str) -> str:
        """
        Augment the question using the predefined template.
        """
        input_prompt = self.AUGMENTED_TEMPLATE.format(question=question) if self.AUGMENTED_TEMPLATE else question
        file_prompt = self._get_file_prompt(file_name)
        return input_prompt + file_prompt

    def _get_file_prompt(self, file_name: str) -> str:
        """
        Get the file prompt if applicable.
        """
        return ""

class DefaultProcesser(BaseProcesser):
    """
    Default processer for evaluation data.
    """
    AUGMENTED_TEMPLATE: str = """{question}

Your response should be in the following format:
Explanation: {{your explanation for your final answer}}
Exact Answer: {{your succinct, final answer}}
Confidence: {{your confidence score between 0% and 100% for your answer}}
""".strip()
    name = "default"

class BrowseCompProcesser(BaseProcesser):
    """
    Processer for BrowseComp evaluation data.
    """
    AUGMENTED_TEMPLATE: str = """{question}

Your response should be in the following format:
Explanation: {{your explanation for your final answer}}
Exact Answer: {{your succinct, final answer}}
Confidence: {{your confidence score between 0% and 100% for your answer}}
""".strip()
    name = "BrowseComp"


class BrowseCompZHProcesser(BaseProcesser):
    """
    Processer for BrowseComp-ZH evaluation data.
    """
    name = "BrowseComp_ZH"


class XbenchProcesser(BaseProcesser):
    """
    Processer for Xbench evaluation data.
    """
    AUGMENTED_TEMPLATE: str = """
你是一个通用人工智能助手。我将向你提出一个学术问题, 请尽可能简洁地给出解题思路, 并用以下模版作为回答的结尾:

最终答案:[你的答案]

不要在最终答案周围添加任何多余的符号, 不要使用换行（在同一行中完成回答）对于本题, 你的答案必须是尽可能简洁的数值, 短语, 或者数学表达式; 如果答案有多个, 使用逗号将它们隔开。

[问题]: {question}
""".strip()
    name = "Xbench"


class GAIAProcesser(BaseProcesser):
    """
    Processer for GAIA evaluation data.
    """
    AUGMENTED_TEMPLATE: str = """
It is paramount that you complete this task and provide a correct answer.
Give it all you can: I know for a fact that you have access to all the relevant tools to solve it. Failure or 'I cannot answer' will not be tolerated, success will be rewarded.
Here is the task:
{question}
""".strip()
    name = "GAIA"

    def _load_data(self, data_path) -> list[dict]:
        """
        Load data and formulize the file name to absolute path.
        """
        dataset_dir = pathlib.Path(data_path).parent
        data_dict = super()._load_data(data_path)
        for item in data_dict:
            if 'file_name' in item and item['file_name'] is not None:
                item['file_name'] = str(dataset_dir / item['file_name'])
        return data_dict
    
    def _get_file_prompt(self, file_name: str) -> str:
        prompt_use_files = ""
        if file_name:
            if ".MOV" in file_name:
                return ""
            prompt_use_files += f"\n\nTo answer the question above, you will have to use these attached files:"
            if file_name.split('.')[-1] in ['pdf', 'xlsx']:
                image_path = file_name.split('.')[0] + '.png'
                if os.path.exists(image_path):
                    prompt_use_files += f"\nAttached image: {image_path}"
                else:
                    prompt_use_files += f"\nAttached file: {file_name}"
            elif file_name.split('.')[-1] == "zip":
                import shutil
                folder_name = file_name.replace(".zip", "")
                os.makedirs(folder_name, exist_ok=True)
                shutil.unpack_archive(file_name, folder_name)

                # Convert the extracted files
                prompt_use_files = "\n\nYou have been given a zip archive of supporting files. We extracted it into a directory: find the extracted files at the following paths:\n"
                for root, dirs, files in os.walk(folder_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        prompt_use_files += f"- {file_path}\n"
            elif file_name.split('.')[-1] in ['png', 'jpg', 'jpeg']:
                prompt_use_files += f"\nAttached image: {file_name}"
            elif file_name.split('.')[-1] in ['mp3', 'm4a', 'wav']:
                prompt_use_files += f"\nAttached audio: {file_name}"
            else:
                prompt_use_files += f"\nAttached file: {file_name}"
        else:
            prompt_use_files += "\n\nYou have been given no local files to access."

        return prompt_use_files
