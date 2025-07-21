from utu.eval.benchmarks import BaseBenchmark
from utu.config import ConfigLoader

config = ConfigLoader.load_eval_config("v00")
benchmark = BaseBenchmark(config)


async def test_benchmark_rollout():
    benchmark.preprocess()
    sample = benchmark.dataset.get_samples("init", limit=1)[0]
    res = await benchmark.rollout_one(sample)
    print(res.as_dict())
