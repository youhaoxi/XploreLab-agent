import argparse
import asyncio

from utu.eval import ExpRunner
from utu.config import ConfigLoader


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="v01", help="Configuration name for evaluation.")
    parser.add_argument("--exp_id", type=str, default=None, help="Experiment ID.")
    args = parser.parse_args()
    
    config = ConfigLoader.load_eval_config(args.config_name)
    if args.exp_id:
        config.exp_id = args.exp_id

    runner = ExpRunner(config)
    asyncio.run(runner.main())
