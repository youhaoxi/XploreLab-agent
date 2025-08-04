import asyncio

from utu.ww.ww_benchmark import WWBenchmark
from utu.eval.utils import parse_eval_config


async def main():
    config = parse_eval_config()
    runner = WWBenchmark(config)
    await runner.judge(stage="rollout")  # set None to rejudge; rollout or judged incrementally
    await runner.stat()


if __name__ == "__main__":
    asyncio.run(main())
