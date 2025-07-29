from utu.eval.benchmarks.ww_benchmark import WWBenchmark
from utu.config import ConfigLoader

config = ConfigLoader.load_eval_config("v00")
benchmark = WWBenchmark(config)


async def test_benchmark_rollout():
    benchmark.preprocess()
    sample = benchmark.dataset.get_samples(limit=1)[0]
    res = await benchmark.rollout_one(sample)
    # print(f"trace_id: {res.trace_id}. response: {res.response}")
    print(res)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_benchmark_rollout())