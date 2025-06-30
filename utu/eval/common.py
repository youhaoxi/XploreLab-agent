import os
import json
import asyncio
import threading
import concurrent.futures
from queue import Queue, Empty
from tqdm import tqdm
from pathlib import Path
from dataclasses import dataclass, asdict
from agents import RunResult, ModelResponse
from agents.models.chatcmpl_converter import Converter

from utu.utils import DIR_ROOT


@dataclass
class EvaluationSample:
    """
    A data class to represent a single evaluation sample.
    """
    source: str  # source benchmark
    raw_question: str
    level: int  # hardness level of the question, if applicable
    augmented_question: str
    correct_answer: str
    file_name: str  # for GAIA
    response: str
    # below for judgement
    extracted_final_answer: str
    judged_response: str
    reasoning: str
    correct: bool
    confidence: int
    # tracing
    time_cost: float = None  # time cost in seconds
    trajectory: list = None  # the agent's reasoning process, a list of messages

    def __init__(self, **kwargs):
        """
        Initialize the EvaluationSample with keyword arguments.
        """
        self.source = kwargs.get('source', '')
        self.raw_question = kwargs.get('raw_question', '')
        self.level = kwargs.get('level', 0)
        self.augmented_question = kwargs.get('augmented_question', '')
        self.correct_answer = kwargs.get('correct_answer', '')
        self.file_name = kwargs.get('file_name', '')
        self.response = kwargs.get('response', None)
        self.extracted_final_answer = kwargs.get('extracted_final_answer', None)
        self.judged_response = kwargs.get('judged_response', None)
        self.reasoning = kwargs.get('reasoning', None)
        self.correct = kwargs.get('correct', None)
        self.confidence = kwargs.get('confidence', None)
        self.trajectory = kwargs.get('trajectory', None)

    def update(self, **kwargs):
        """
        Update the evaluation sample with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get(self, key, default=None):
        """
        Get the value of the specified key, or return default if not found.
        """
        return getattr(self, key, default)
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create an EvaluationSample from a dictionary.
        """
        return cls(**data)
    
    def as_dict(self) -> dict:
        # only contain fields that are not None
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class EvaluationResult:
    """
    A data class to represent the result of an evaluation.
    """
    benchmark: str
    metrics: dict

    def update(self, **kwargs):
        """
        Update the evaluation result with the given keyword arguments.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def as_dict(self):
        """
        Convert the evaluation result to a dictionary.
        """
        return {
            "benchmark": self.benchmark,
            "metrics": self.metrics
        }


# 限制并发数量的装饰器
def limit_concurrency(max_concurrent: int):
    semaphore = asyncio.Semaphore(max_concurrent)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await func(*args, **kwargs)
        return wrapper
    return decorator

# 限制线程级并发数量的装饰器
def limit_concurrency_thread(max_concurrent: int):
    semaphore = threading.Semaphore(max_concurrent)

    def decorator(func):
        def wrapper(*args, **kwargs):
            with semaphore:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# 将线程中的异步函数转换为同步函数的转换器
def async_to_sync(func):
    def wrapper(index, *args, **kwargs):
        result = asyncio.run(func(*args, **kwargs))
        return index, result
    return wrapper


async def process_with_threading(
                                 thread_func,
                                 save_func,
                                 samples: list[EvaluationSample], 
                                 thread_size: int, 
                                 save_freq: int = 10, 
                                 save_path: str = None):
    """
    Process the samples using a fixed-size thread pool.
    """
    # 初始化缓存队列
    data_queue = Queue()
    for i, sample in enumerate(samples):
        data_queue.put((i, sample))
    
    # 初始化杂项
    results = {}  # 输出缓存
    saved_count = 0  # 记录当前进度
    continuous_results = []  # 待保存的连续输出结果序列
    tbar = tqdm(total=len(samples), desc="Processing")

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_size) as executor:
        futures = {executor.submit(thread_func, *data_queue.get()): _ for _ in range(min(thread_size, data_queue.qsize()))}

        while futures:
            # 等待任何一个任务完成
            done, futures = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)

            # 同步已完成的任务
            for future in done:
                index, result = future.result()  # 获取index和结果
                results[index] = result  # 将结果添加到输出缓存
                
                # 从缓存中取出连续的结果
                for i in range(saved_count, len(samples)):
                    if i in results:
                        continuous_results.append(results[i])
                        saved_count += 1
                        tbar.update(1)
                        del results[i]
                    else:
                        break

                # 保存连续的结果（如果提供了保存路径和频率）
                if save_path and len(continuous_results) >= save_freq:
                    await save_func(continuous_results, save_path)
                    # 重置连续结果序列
                    continuous_results = []
                
                # 向线程池中补充新任务
                try:
                    new_data = data_queue.get_nowait()
                    new_future = executor.submit(thread_func, *new_data)
                    futures.add(new_future)
                # 直到数据全跑完
                except Empty:
                    pass

    # 保存剩余的结果
    final_results = []
    # 清空连续结果序列
    if continuous_results:
        final_results.extend(continuous_results)
        if save_path:
            await save_func(continuous_results, save_path)
    # 清空缓存
    if results:
        remaining_results = []
        for index in sorted(list(results.keys())):
            remaining_results.append(results[index])
            final_results.append(results[index])
            del results[index]
            tbar.update(1)
        if save_path:
            await save_func(remaining_results, save_path)
    
    tbar.close()
    
    # 按原始顺序返回结果
    if not final_results:
        final_results = continuous_results
    
    return final_results


def get_trajectory_from_agent_result(agent_result: RunResult) -> list[dict]:
    messages = Converter.items_to_messages(agent_result.to_input_list())
    trajectory = [dict(message) for message in messages]
    model_responses = agent_result.raw_responses
    usage_list = []
    for model_response in model_responses:
        usage_list.append(asdict(model_response.usage))
    # 添加模型响应的使用情况
    usage_idx = 0
    for i, message in enumerate(trajectory):
        if message.get("role") == "assistant":
            if usage_idx < len(usage_list):
                curr_usage = usage_list[usage_idx]
                message["usage"] = {"input_tokens": curr_usage["input_tokens"],
                                    "output_tokens": curr_usage["output_tokens"],
                                    "total_tokens": curr_usage["total_tokens"],
                                    "requests": curr_usage["requests"]}
                usage_idx += 1
            else:
                message["usage"] = {}
    return trajectory


# 内置benchmarks
BUILTIN_BENCHMARKS = {
    "GAIA_val": {
        "data_path": DIR_ROOT / "data" / "gaia" / "val.jsonl",
        "type": "single",
        "processer": "GAIA",
        "evaluator": "GAIA",
        "description": "GAIA validation set for evaluation"
    },
    "GAIA_test": {
        "data_path": DIR_ROOT / "data" / "gaia" / "test.jsonl",
        "type": "single",
        "processer": "GAIA",
        "evaluator": "GAIA",
        "description": "GAIA test set for evaluation"
    },
    "BrowseComp": {
        "data_path": DIR_ROOT / "data" / "browse_comp" / "test.jsonl",
        "type": "single",
        "processer": "BrowseComp",
        "evaluator": "BrowseComp",
        "description": "BrowseComp benchmark for evaluation"
    },
    "BrowseComp_ZH": {
        "data_path": DIR_ROOT / "data" / "browse_comp_zh" / "test.jsonl",
        "type": "single",
        "processer": "BrowseComp_ZH",
        "evaluator": "BrowseComp_ZH",
        "description": "BrowseComp Chinese benchmark for evaluation"
    },
    "XBench": {
        "data_path": DIR_ROOT / "data" / "xbench" / "test.jsonl",
        "type": "single",
        "processer": "XBench",
        "evaluator": "XBench",
        "description": "XBench benchmark for evaluation"
    }
}
