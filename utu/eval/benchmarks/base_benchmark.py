import asyncio
import json
import logging
import time
import traceback

from tqdm import tqdm

from ...utils import set_log_level
from ...config import EvalConfig, ConfigLoader
from ...agents import UTUSimpleAgent, build_agent
from ..data import DBDataManager, EvaluationSample, EvaluationResult
from ..evaluation import BaseEval, EVAL_FACTORY
from ..common import get_trajectory_from_agent_result

set_log_level("WARNING")
logger = logging.getLogger(__name__)



class BaseBenchmark:
    dataset: DBDataManager
    total_tokens: int = 0
    _source_to_judge: dict[str, BaseEval] = {}
    _source_to_agent: dict[str, UTUSimpleAgent] = {}

    def __init__(self, config: EvalConfig|str) -> None:
        # config
        if isinstance(config, str): config = ConfigLoader.load_eval_config(name=config)
        self.config = config
        
        # dataset
        self.dataset = DBDataManager(config)
        self.dataset.load()


    async def main(self):

        print(f"> Running with config: {self.config}")
        # overall_start_time = time.time()
        print(f"> Running rollout...")
        await self.rollout()
        # time_cost = time.time() - overall_start_time; tokens = self.total_tokens
        # print(f"Processed {tokens} tokens in {time_cost:.2f} seconds.")
        # print(f"The average inference speed is {tokens / time_cost:.2f} tokens/second.")
        # print((f"total tokens: {tokens}, time cost: {time_cost:.2f}, avg_speed: {tokens / time_cost:.2f}\n"))
        # 4. evaluate the results
        print(f"> Running judge...")
        await self.judge()
        print(f"> Running stat...")
        await self.stat()


    async def rollout(self) -> None:
        samples = self.dataset.get_samples(stage="init")
        print(f"Rollout {len(samples)} samples...")

        semaphore = asyncio.Semaphore(self.config.concurrency)
        async def rollout_with_semaphore(item: EvaluationSample):
            async with semaphore:
                try:
                    return await self.rollout_one(item)
                except Exception as e:
                    print(f">>>>>>>>>>>>>\nError running rollout on sample '{item.raw_question}': {e}\n<<<<<<<<<<<<<")
                    traceback.print_exc()
        tasks = [rollout_with_semaphore(item) for item in samples]
        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Rolling out"):
            result = await task
            if result is not None:
                results.append(result)
        print(f"Successfully rollout {len(results)} samples. Updated to db.")
        return results

    async def rollout_one(self, sample: EvaluationSample) -> EvaluationSample:
        agent = await self._get_agent(sample.source)
        start_time = time.time()
        result = await agent.run(sample.augmented_question)
        end_time = time.time()
        predicted_answer = result.final_output

        # Update the sample with the predicted answer and trajectory
        trajectory = get_trajectory_from_agent_result(result)
        sample.update(
            response=predicted_answer,
            time_cost=end_time - start_time,
            trajectory=json.dumps(trajectory, ensure_ascii=False),
            stage="rollout"  # update stage to rollout!
        )
        self.dataset.save(sample)
        # update the total tokens
        self.total_tokens += sum([step.get("usage", {}).get("total_tokens", 0) for step in trajectory])
        return sample

    async def _get_agent(self, source) -> UTUSimpleAgent:
        if source not in self._source_to_agent:
            instructions = self._get_judge(source).get_instructions()
            agent = build_agent(self.config.agent, name=f"{source}-agent", instructions=instructions)
            await agent.build()
            self._source_to_agent[source] = agent
        return self._source_to_agent[source]

    async def judge(self) -> list[EvaluationSample]:
        samples = self.dataset.get_samples(stage="rollout")
        print(f"Judging {len(samples)} samples...")

        semaphore = asyncio.Semaphore(self.config.judge_concurrency)
        async def judge_with_semaphore(item: EvaluationSample):
            async with semaphore:
                try:
                    return await self.judge_one(item)
                except Exception as e:
                    print(f">>>>>>>>>>>>>\nError judging sample '{item}': {e}\n<<<<<<<<<<<<<")
                    traceback.print_exc()
                    return None
        tasks = [judge_with_semaphore(item) for item in samples]
        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Judging"):
            result = await task
            if result is not None:
                results.append(result)
        print(f"Successfully judged {len(results)} samples. Updated to db.")
        return results

    async def judge_one(self, data: EvaluationSample) -> EvaluationSample:
        judger = self._get_judge(data.source)
        result = await judger.judge_one(data)
        result.update(stage="judged")  # update stage to judged
        self.dataset.save(result)
        return result

    def _get_judge(self, source: str) -> BaseEval:
        if source not in self._source_to_judge:
            self._source_to_judge[source] = EVAL_FACTORY.get(source, self.config)
        return self._source_to_judge[source]

    async def stat(self):
        # TODO: wrap the data like @verl / @torch
        # TODO: log to wandb
        judged_samples = self.dataset.get_samples(stage="judged")
        print(f"Stat from {len(judged_samples)} samples:")

        data_by_benchmark = self._group_data_by_benchmark(judged_samples)
        overall_results: list[EvaluationResult] = []
        for benchmark, data in data_by_benchmark.items():
            evaluator = self._get_judge(benchmark)
            result = await evaluator.stat(data)
            result.update(benchmark=benchmark)
            overall_results.append(result)

        print(json.dumps([r.as_dict() for r in overall_results], indent=4, ensure_ascii=False))

    def _group_data_by_benchmark(self, predict_data: list[EvaluationSample]) -> dict[str, list[EvaluationSample]]:
        # group data by benchmark
        data_by_benchmark: dict[str, list[EvaluationSample]] = {}
        for data in predict_data:
            benchmark = data.source
            if benchmark not in data_by_benchmark:
                data_by_benchmark[benchmark] = []
            data_by_benchmark[benchmark].append(data)
        return data_by_benchmark
