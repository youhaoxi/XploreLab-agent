import asyncio

from utu.agents.ww_searcher import SearcherAgent
from utu.config import ConfigLoader

search_config = ConfigLoader.load_agent_config("search_agent")
search_agent = SearcherAgent(search_config)
query = "在长安大学信息工程学院徐志刚教授指导的两篇在《Transportation Research Part C》上发表的交通运输学科论文中，各篇的第一作者分别是谁？"
background = "徐志刚教授是长安大学信息工程学院副院长、博士生导师，国家级高层次人才，主要研究方向为车联网与智能交通系统，担任多个学术职务并发表重要研究成果。Transportation Research Part C是一本专注于交通系统与新兴技术的高质量学术期刊，涵盖该领域的开发、应用及影响，属于工程技术领域的顶级期刊。"


async def test_search_agent():
    await search_agent.build()
    search_result = asyncio.run(search_agent.research(query, background))
    print("query:", query)
    print("final_output:", search_result.output)
    print("search_results:", search_result.search_results)
    print("trajectory:", search_result.trajectory)
