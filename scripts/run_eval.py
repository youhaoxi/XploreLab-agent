import argparse
import asyncio

from utu.eval import ExpRunner


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="v0.1", help="Configuration name for evaluation.")
    args = parser.parse_args()
    runner = ExpRunner(args.config_name)
    asyncio.run(runner.main())
