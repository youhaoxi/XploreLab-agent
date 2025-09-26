import asyncio
import datetime
import argparse
from utu.agents import SimpleAgent
from utu.config import ConfigLoader

from fill_template import fill_template, extract_json

config = ConfigLoader.load_agent_config("examples/ppt_generator.yaml")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str)
    args = parser.parse_args()
    
    agent = SimpleAgent(config=config)
    await agent.build()
    
    if args.file:
        with open(args.file, "r") as f:
            html = f.read()
    else:
        html = "https://arxiv.org/html/2509.20234v1"
    
    query = f"""
    把这个网页做成18页左右的PPT。如果是论文，要求按照学术报告的风格来做PPT：
    
    {html}
    """
    
    result = await agent.run(query)
    final_result = result.final_output
    print(final_result)
    
    with open("output.json", "w") as f:
        f.write(final_result)
    
    json_data = extract_json(final_result)
    fill_template("template/template_ori.pptx", f"output-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.pptx", json_data)

if __name__ == "__main__":
    asyncio.run(main())