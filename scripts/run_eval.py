import argparse
import asyncio

from utu.eval import BaseBenchmark
from utu.config import ConfigLoader, EvalConfig


def parse() -> EvalConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="v01", help="Configuration name for evaluation.")
    parser.add_argument("--exp_id", type=str, default=None, help="Experiment ID.")
    parser.add_argument("--agent_model", type=str, default=None, help="Agent model.")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset.")
    args = parser.parse_args()
    
    config = ConfigLoader.load_eval_config(args.config_name)
    if args.exp_id:
        config.exp_id = args.exp_id
    if args.agent_model:
        config.agent.model.model = args.agent_model
    if args.dataset:
        config.dataset = args.dataset
    return config

async def main():
    config = parse()
    runner = BaseBenchmark(config)
    await runner.main()

if __name__ == "__main__":
    asyncio.run(main())
