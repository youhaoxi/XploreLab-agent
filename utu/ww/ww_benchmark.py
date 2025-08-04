import time
import json

from ..eval.benchmarks.base_benchmark import BaseBenchmark
from ..eval.data import EvaluationSample
from .ww_agent import WWAgent


class WWBenchmark(BaseBenchmark):
    """ 复用现有逻辑, 重写 agent, process, rollout 逻辑 """
    def preprocess_one(self, sample: EvaluationSample) -> EvaluationSample:
        aug_question = f"{sample.raw_question}\nReference url: {sample.meta['root_url']}"
        sample.update(augmented_question=aug_question)
        self.dataset.save(sample)
        return sample

    async def _get_agent(self) -> WWAgent:
        # init a new agent for each rollout!
        agent = WWAgent(self.config.agent)
        await agent.build()
        return agent

    async def rollout_one(self, sample: EvaluationSample) -> EvaluationSample:
        agent = await self._get_agent()
        start_time = time.time()
        result = await agent.run(sample.augmented_question)
        end_time = time.time()

        # Update the sample with the predicted answer and trajectory
        if not isinstance(result.trajectory, str):
            result.trajectory = json.dumps(result.trajectory, ensure_ascii=False)
        sample.update(
            trace_id=result.trace_id,
            response=result.final_output,
            time_cost=end_time - start_time,
            trajectory=result.trajectory,
            stage="rollout"  # update stage to rollout!
        )
        self.dataset.save(sample)
        # update the total tokens
        # self.total_tokens += sum([step.get("usage", {}).get("total_tokens", 0) for step in trajectory])
        return sample
