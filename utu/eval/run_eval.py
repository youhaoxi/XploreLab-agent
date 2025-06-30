import time
import asyncio
import pathlib
import os, json
import aiofiles
from agents import RunResult, AgentsException
from agents.models.chatcmpl_converter import Converter
from typing import Literal, List, Tuple, Union

from utu.utils import DIR_ROOT
from utu.config import EvalConfig
from utu.agents import UTUSimpleAgent
from utu.eval import BaseProcesser, DATA_PROCESSER_FACTORY, MixedProcesser
from utu.eval import BaseEval, EVAL_FACTORY, MixedEval
from utu.eval.common import limit_concurrency, limit_concurrency_thread, async_to_sync, process_with_threading
from utu.eval.common import BUILTIN_BENCHMARKS, EvaluationSample, EvaluationResult


flock = asyncio.Lock()
DIR_EVAL_OUT = DIR_ROOT / "utu" / "eval" / "output"
pathlib.Path(DIR_EVAL_OUT).mkdir(parents=True, exist_ok=True)   # 创建输出目录


async def build_agent(name: str, instructions: str) -> UTUSimpleAgent:
    # load the builtin simple agent
    agent = UTUSimpleAgent(name=name, instructions=instructions)
    await agent.build()
    return agent


async def load_data(data_path: str, processer_name: str, config: EvalConfig) -> List[EvaluationSample]:
    """
    Load and process data from the specified path using the given processer.
    """
    if processer_name == "mixed":
        processer = MixedProcesser(config)
    else:
        processer = DATA_PROCESSER_FACTORY.get(processer_name, config)
    samples = await processer.load_and_process(data_path)
    return samples


async def save_results(results: List[EvaluationSample], save_path: str):
    """
    Save samples to the target file
    """
    async with flock:
        async with aiofiles.open(save_path, "a+") as f:
            for result in results:
                await f.write(json.dumps(result.as_dict(), ensure_ascii=False) + "\n")


async def main(config: EvalConfig):
    # 1. load and prepare the data
    # 1.1 get the dataset path and corresponding processer
    if config.type == "single":
        if config.dataset in BUILTIN_BENCHMARKS:
            # load builtin benchmark
            dataset_info = BUILTIN_BENCHMARKS[config.dataset]
            data_path = str(dataset_info["data_path"])
            processer_name = dataset_info["processer"]
            evaluator_name = dataset_info["evaluator"]
        else:
            data_path = config.dataset
            processer_name = "default"
            evaluator_name = "default"
    else:
        # mixed dataset
        data_path = config.dataset
        processer_name = "mixed"
        evaluator_name = "mixed"
    # if assign a specific evalution method, use the corresponding processer and evaluator
    if config.eval_method:
        processer_name = config.eval_method
        evaluator_name = config.eval_method
    # 1.2 load the data
    samples = await load_data(data_path, processer_name, config)
    samples = samples[:1]
    print(f"Loaded {len(samples)} samples from '{config.dataset}' using processer '{processer_name}'.")

    # 2. get the agents and evaluators
    # 2.1 prepare the evaluator config(especially for LLM judgement)
    # 2.2 get evaluator and agent instructions
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
        agents[name] = await build_agent(name=f"{name}-agent", instructions=instructions)
    
    # 3. rollout with thread pool
    # 3.1 define the thread function
    @limit_concurrency_thread(CONCURRENCY)
    def run_agent(agent: UTUSimpleAgent, query: str) -> RunResult:
        """
        Run the agent on the given query and return the result.
        """
        # print(f"Running agent '{agent.name}' on query '{query}'...")
        # run the agent
        try:
            result = asyncio.run(agent.run(query))
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
    
    def rollout(index: int, sample: EvaluationSample) -> Tuple[int, EvaluationSample]:
        """
        Run the agent on the sample and return the updated sample with predictions.
        """
        agent = agents[sample.source]  # Get the agent for the sample's source
        start_time = time.time()
        result = run_agent(agent, sample.augmented_question)
        end_time = time.time()
        predicted_answer = result.final_output

        # Update the sample with the predicted answer and trajectory
        sample.update(
            response=predicted_answer,
            time_cost=end_time - start_time,
            trajectory=Converter.items_to_messages(result.to_input_list())
        )
        return index, sample
    
    # 3.2 sync the thread function and put it into the thread pool
    # 3.3 run the rollout with threading
    output_file = str(DIR_EVAL_OUT / config.output_file)
    existing_samples = []
    samples_to_rollout = samples
    if os.path.exists(output_file):
        # resume from the last output file
        print(f"Output file '{output_file}' already exists. Resuming from the last output...")
        async with aiofiles.open(output_file, "r") as f:
            existing_samples = [EvaluationSample.from_dict(json.loads(line.strip())) async for line in f]
        # filter out the samples that are already rolled out
        existing_questions = [sample.raw_question for sample in existing_samples]
        samples_to_rollout = [sample for sample in samples if sample.raw_question not in existing_questions]
        print(f"Resumed {len(existing_samples)} existing samples. Remaining samples to rollout: {len(samples_to_rollout)}.")
    print(f"Rolling out {len(samples_to_rollout)} samples with {THREAD_POOL_SIZE} threads...")
    rollout_samples = await process_with_threading(
        thread_func=rollout,
        save_func=save_results,
        samples=samples_to_rollout,
        thread_size=THREAD_POOL_SIZE,
        save_freq=5,  # Save every 10 samples
        save_path=output_file   # Save the output to the output file
    )
    print(f"Rolled out {len(rollout_samples)} samples.")
    rollout_samples.extend(existing_samples)  # Combine the rolled out samples with existing ones

    # 4. evaluate the results
    judged_data, eval_result = await evaluator.eval(
        predict_data=rollout_samples,
        judge_with_threading=True  # Use threading for judgement
    )
    print(f"Evaluated {len(judged_data)} samples.")
    # print the evaluation result
    print("Evaluation result:")
    print(json.dumps(eval_result.as_dict(), indent=4, ensure_ascii=False))
    # save the judged data and evaluation result
    judge_output_file = str(DIR_EVAL_OUT / config.judge_output_file)
    metrics_file = str(DIR_EVAL_OUT / config.metrics_file)
    async with aiofiles.open(judge_output_file, "w") as f:
        for sample in judged_data:
            await f.write(json.dumps(sample.as_dict(), ensure_ascii=False) + "\n")
    with open(metrics_file, "w") as f:
        json.dump(eval_result.as_dict(), f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    import argparse
    from utu.config import ConfigLoader

    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="default", help="Configuration name for evaluation.")
    args = parser.parse_args()

    # Load the configuration
    # config_path = DIR_ROOT / "configs" / f"{args.config_name}.yaml"
    config = ConfigLoader.load_eval_config(name=args.config_name)
    
    # Set the global thread pool size
    global THREAD_POOL_SIZE, CONCURRENCY
    THREAD_POOL_SIZE = config.thread_pool_size
    CONCURRENCY = config.concurrency

    # Run the evaluation
    asyncio.run(main(config))
