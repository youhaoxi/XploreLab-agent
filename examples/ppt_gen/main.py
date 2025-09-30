import argparse
import asyncio
import datetime

from fill_template import extract_json, fill_template

from utu.agents import SimpleAgent
from utu.config import ConfigLoader

config = ConfigLoader.load_agent_config("examples/ppt_generator.yaml")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str)
    args = parser.parse_args()

    agent = SimpleAgent(config=config)
    await agent.build()

    if args.file:
        with open(args.file) as f:
            html = f.read()
    else:
        html = "https://arxiv.org/html/2509.20234v1"

    query = f"""
    把这个网页做成18页左右的PPT。如果是论文，要求按照学术报告的风格来做PPT；如果不是论文，就按照普通PPT的方式来做：

    {html}
    """

    # query = """
    # 收集有关夜鹭的信息，整理成演讲PPT。
    # """

    result = await agent.chat_streamed(query)
    final_result = result.final_output
    print(final_result)

    with open("output.json", "w") as f:
        f.write(final_result)

    json_data = extract_json(final_result)
    fill_template(
        template_path="template/template_ori.pptx",
        output_path=f"output-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pptx",
        json_data=json_data,
    )


if __name__ == "__main__":
    asyncio.run(main())
