import asyncio
import json
import argparse

import pandas as pd

from utu.eval.data_manager.db_data_manager import DBDataManager
from utu.config import ConfigLoader, EvalConfig


async def get_stat(config: EvalConfig):
    db = DBDataManager(config)
    samples = await db.get_samples()
    df = pd.DataFrame([sample.as_dict() for sample in samples])
    # stat data group by stage
    stat = df.groupby("stage").size()
    print(stat)


async def dump_exp_samples(config: EvalConfig, output_file: str, clear_records: bool = False):
    db = DBDataManager(config)
    samples = await db.get_samples()
    print(f"Found {len(samples)} samples in db.")
    with open(output_file, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample.as_dict(), ensure_ascii=False) + "\n")
    if clear_records:
        print(f"Clearing {len(samples)} samples from db.")
        await db.delete_samples(samples)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_name", type=str, default="v01", help="Configuration name for evaluation.")
    parser.add_argument("--op", type=str, choices=["stat", "dump"], default="dump", help="Option to run.")
    parser.add_argument("--exp_id", type=str, default=None, help="Experiment ID.")
    parser.add_argument("--output_file", type=str, default=None, help="Output file.")
    parser.add_argument("--clear_records", action="store_true", help="Clear records from db.")
    args = parser.parse_args()
    
    config = ConfigLoader.load_eval_config(args.config_name)
    if args.exp_id:
        config.exp_id = args.exp_id

    if not args.output_file:
        args.output_file = f"data/output_{config.exp_id}.jsonl"
    
    match args.op:
        case "stat":
            await get_stat(config)
        case "dump":
            await dump_exp_samples(config, output_file=args.output_file, clear_records=args.clear_records)


if __name__ == "__main__":
    asyncio.run(main())