from datetime import datetime
from utu.ww.planner import PlannerAgent


planner = PlannerAgent()

test_queries = [
    {
        "mode": "planning",
        "question": "蔺佳哲博士在2022年4月13日西南科技大学的学术报告中介绍了哪种预测精度高于1%的气动特性快速预测模型？",
        "background_info": "西南科技大学在2022年4月举办了一系列学术报告活动。",
    },
    {
        "mode": "update_planning",
        "question": "蔺佳哲博士在2022年4月13日西南科技大学的学术报告中介绍了哪种预测精度高于1%的气动特性快速预测模型？",
        "background_info": "西南科技大学在2022年4月举办了一系列学术报告活动。",
        "previous_plan": "",
        "task": "搜索2022年4月13日西南科技大学举办的学术报告信息，特别是蔺佳哲博士的报告",
        "task_results": "找到了西南科技大学2022年4月13日的学术报告记录，确认蔺佳哲博士进行了关于气动特性预测模型的报告，但具体模型信息需要进一步搜索。",
    },
]
session_id = datetime.now().isoformat()


async def test_planner():
    for query in test_queries:
        res = await planner.execute_planning(**query, session_id=session_id)
        print(res)
