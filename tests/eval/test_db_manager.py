import uuid
from utu.eval.data_manager.db_data_manager import DBDataManager
from utu.config import EvalConfig, ConfigLoader

config = ConfigLoader.load_eval_config("default")
config.exp_id = f"test_{uuid.uuid4()}"  # ensure unique
db_manager = DBDataManager(config)

async def test_db_manager():
    data = await db_manager.init()
    print(f"Load {len(data)} samples")
    data_state1 = await db_manager.get_samples()
    print(f"Get {len(data_state1)} samples from `init` stage")
    sample_updated = data_state1[0]
    sample_updated.update(response="test", stage="rollout")
    await db_manager.update_samples(sample_updated)
    data_state2 = await db_manager.get_samples("rollout")
    print(f"Get {len(data_state2)} samples from `rollout` stage")

