import os
import json
import aiofiles

from ...config import EvalConfig
from ..data import EvaluationSample
from . import BaseProcesser, DATA_PROCESSER_FACTORY


class MixedProcesser:
    """
    Class to process data from different benchmarks.
    """
    config: EvalConfig
    _processers: dict[str, BaseProcesser]  # cache processers for different benchmarks

    def __init__(self, config):
        self._processers = {}
        self.config = config or EvalConfig()
    
    async def load_and_process(self, data_path: str) -> list[EvaluationSample]:
        """
        Asynchronously load and process data from the specified path using the appropriate processer.
        """
        data_dict = await self._load_data(data_path)
        samples = []
        for item in data_dict:
            source = item.get("source", "")
            if source and source not in self._processers:
                processer = DATA_PROCESSER_FACTORY.get(source, self.config)
                self._processers[source] = processer
            processer = self._processers.get(source, DATA_PROCESSER_FACTORY.get("default", self.config))
            sample = processer.process_one(item)
            samples.append(sample)
        return samples

    async def _load_data(self, data_path: str) -> list[dict]:
        """
        Asynchronously load data from different formats.
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
