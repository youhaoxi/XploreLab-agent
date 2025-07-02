from utu.eval.data_processer import MixedProcesser
from utu.config import ConfigLoader

config = ConfigLoader.load_eval_config("default")
processer = MixedProcesser(config)

async def test_processor_mixed():
    samples = await processer.load_and_process("data/utu_test/agent_test.jsonl")
    print(f"Loaded {len(samples)} samples.")
    print(f"First sample: {samples[0].as_dict()}")
