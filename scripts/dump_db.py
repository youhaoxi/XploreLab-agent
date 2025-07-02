import asyncio
import json
from utu.eval.data_manager.db_data_manager import DBDataManager
from utu.config import ConfigLoader


config = ConfigLoader.load_eval_config("v0.1")

async def dump_exp_samples(exp_id: str, output_file: str):
    config.exp_id = exp_id
    db = DBDataManager(config)
    samples = await db.get_samples(stage="init")
    with open(output_file, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample.as_dict(), ensure_ascii=False) + "\n")

if __name__ == "__main__":
    asyncio.run(dump_exp_samples(config.exp_id, "dumped_samples.jsonl"))
