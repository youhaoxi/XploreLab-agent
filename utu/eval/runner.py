""" 
- [x] refactor run_eval.py
- [x] abstract DataManager, ExpRunner
- [x] connect data to db -- support better analysis
- [ ] config: add agent configs in eval config; save config with exp_id
"""

import time
import asyncio
import json
import logging
from typing import List

from tqdm import tqdm
from agents import RunResult, AgentsException

from ..config import EvalConfig, ConfigLoader, AgentConfig
from ..agents import UTUSimpleAgent, build_agent
from ..utils import set_log_level
from ..eval import  EVAL_FACTORY, MixedEval, BaseEval
from ..eval.common import get_trajectory_from_agent_result
from .data_manager.db_data_manager import DBDataManager, EvaluationSampleSQL

set_log_level("WARNING")
logger = logging.getLogger(__name__)


class ExpRunner:
    agents: dict[str, UTUSimpleAgent]
    evaluator: BaseEval
    data_manager: DBDataManager
    total_tokens: int = 0

    def __init__(self, config: EvalConfig|str):
        if isinstance(config, str):
            config = ConfigLoader.load_eval_config(name=config)
        self.config = config

    async def main(self):
        # 1. load and prepare the data
        # 2. get the agents and evaluators
        print(f"> Running with config: {self.config}")
        await self.init(self.config)
        # 3. rollout
        data_to_rollout = await self.data_manager.get_samples(stage="init")
        overall_start_time = time.time()
        await self.rollout(data_to_rollout)
        time_cost = time.time() - overall_start_time; tokens = self.total_tokens
        print(f"Processed {tokens} tokens in {time_cost:.2f} seconds.")
        print(f"The average inference speed is {tokens / time_cost:.2f} tokens/second.")
        print((f"total tokens: {tokens}, time cost: {time_cost:.2f}, avg_speed: {tokens / time_cost:.2f}\n"))
        # 4. evaluate the results
        all_samples = await self.data_manager.get_samples(stage="rollout")
        judged_data = await self.evaluator.eval(all_samples)
        for data in judged_data:
            data.update(stage="judged")
        await self.data_manager.update_samples(judged_data)
        print(f"Evaluated {len(judged_data)} samples.")
        # 5. Stat the results
        judged_samples = await self.data_manager.get_samples(stage="judged")
        eval_result = await self.evaluator.stat(judged_samples)
        print(f"Stat from {len(judged_samples)} samples:")
        print(json.dumps(eval_result.as_dict(), indent=4, ensure_ascii=False))


    async def init(self, config: EvalConfig):
        self.data_manager = DBDataManager(config)
        data_path, processer_name, evaluator_name = self.data_manager._parse_config()
        samples = await self.data_manager.init()
        print(f"Loaded {len(samples)} samples from '{config.dataset}' using processer '{processer_name}'.")
        if evaluator_name == "mixed":
            sources = set(sample.source for sample in samples)
            evaluator = MixedEval(sources, config)
            agent_instructions = evaluator.get_instructions()
        else:
            evaluator = EVAL_FACTORY.get(evaluator_name, config)
            agent_instructions = {evaluator_name: evaluator.get_instructions()}
        
        # 2.3 build the agents
        agents = {}
        for name, instructions in agent_instructions.items():
            agents[name] = await self.build_agent(config.agent, name=f"{name}-agent", instructions=instructions)
        
        self.agents = agents
        self.evaluator = evaluator

    async def build_agent(self, config: AgentConfig|str, name: str, instructions: str) -> UTUSimpleAgent:
        agent = build_agent(config, name=name, instructions=instructions)
        await agent.build()
        return agent

    async def rollout(self, samples: List[EvaluationSampleSQL]) -> list[EvaluationSampleSQL]:
        semaphore = asyncio.Semaphore(self.config.concurrency)
        async def rollout_with_semaphore(item: EvaluationSampleSQL):
            async with semaphore:
                try:
                    return await self.rollout_single(item)
                except Exception as e:
                    message = f"Error running rollout on sample '{item.raw_question}': {e}"
                    return {"error": message}
        tasks = [rollout_with_semaphore(item) for item in samples]
        results = []
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Rolling out"):
            result = await task
            if isinstance(result, dict) and "error" in result:
                logger.error(result)
            else:
                await self.data_manager.update_samples(result)
                results.append(result)
        print(f"Rollout {len(results)} samples. Updated to db.")
        return results

    async def rollout_single(self, sample: EvaluationSampleSQL) -> EvaluationSampleSQL:
        """
        Run the agent on the sample and return the updated sample with predictions.
        """
        agent = self.agents[sample.source]  # Get the agent for the sample's source
        start_time = time.time()
        result = await self._run_agent(agent, sample.augmented_question)
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
        # update the total tokens
        self.total_tokens += sum([step.get("usage", {}).get("total_tokens", 0) for step in trajectory])
        return sample

    async def _run_agent(self, agent: UTUSimpleAgent, query: str) -> RunResult:
        """
        Run the agent on the given query and return the result.
        """
        try:
            result = await agent.run(query)
        except AgentsException as e:
            print(f"Error running agent '{agent.name}' on query '{query}': {e}")
            result = RunResult(
                input=e.run_data.input,
                new_items=e.run_data.new_items,
                raw_responses=e.run_data.raw_responses,
                final_output=e.message or "",
                _last_agent=e.run_data.last_agent,
                input_guardrail_results=e.run_data.input_guardrail_results,
                output_guardrail_results=e.run_data.output_guardrail_results,
                context_wrapper=e.run_data.context_wrapper
            )
            return result
        return result
