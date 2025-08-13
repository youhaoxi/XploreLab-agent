"""from @ian"""

import re
import json
import asyncio
from datetime import datetime

from ...tools import SearchToolkit
from ...utils import SimplifiedAsyncOpenAI, async_file_cache, oneline_object, get_logger

logger = get_logger(__name__)


step1_prompt = """Your task is to act as a helpful AI Language Model (LLM) to assist users in generating search queries for information you are not familiar with. Your goal is to determine if you have enough knowledge about the concepts mentioned in the user's query. If you do, no query will be generated. If not, you will create search queries for the very basic information about these concepts.
Current date: {current_date}

First, please carefully read the user's query:
<Query>
{user_query}
</Query>

When generating queries, please follow these rules:
1. Identify the key noun concepts in the user's query that you may not be familiar with.
2. Only generate queries that ask for basic information, such as "What is [concept]?" or "[concept]?". Do not generate queries that ask for detailed comparisons or specific features.
3. Only generate queries that are necessary to understand the concepts at a basic level. If you already know enough about all the concepts, do not generate any queries.
4. The language of the queries should match the language of the user's query.

Please output a JSON object containing the following fields:
{{
    "in_your_knowledge": true/false,  # Indicates whether you have enough knowledge about all the concepts in the query,
    "queries": []  # (Optional) A list of queries to search for basic information about concepts you do not have enough knowledge about
}}
Start your response now."""

step2_prompt = """Your task is to provide concise explanations based on search engine results. You will receive search queries and their corresponding search results, and your goal is to extract and summarize the most essential information about the queried concepts.
Current date: {current_date}

You will be given:
<Queries>
{queries}
</Queries>

<Search_Results>
{search_results}
</Search_Results>

Please follow these guidelines:
1. For each query, provide a brief 1 sentence explanation that captures the core definition or essence of the concept.
2. Focus on the most fundamental and widely accepted information from the search results.
3. Keep explanations simple and accessible, avoiding overly technical jargon.
4. If multiple queries are provided, address each one in sequence.
5. Use the same language as the original queries.
6. If the search results are insufficient or unclear, state that clearly.
7. If there exist duplicate queries, only provide one explanation for that query.
8. Provide the explanations of the queries without repeating the query itself.
9. Keep your response concise, limiting it to 100 words maximum.

Provide your explanations in a natural paragraph format.

Start your response now."""


class ModuleGenBackground:
    def __init__(self):
        self.step1_prompt = step1_prompt
        self.step2_prompt = step2_prompt
        self.search_tool_instance = SearchToolkit()
        self.model = SimplifiedAsyncOpenAI()

    def _extract_and_load_json(self, text: str) -> dict:
        try:
            extracted_json = (
                re.search(r"\{.*\}", text, re.DOTALL).group(0) if re.search(r"\{.*\}", text, re.DOTALL) else None
            )
            try_load_json = json.loads(extracted_json)
            assert "queries" in try_load_json
            assert "in_your_knowledge" in try_load_json
            return try_load_json
        except AssertionError:
            logger.error(f"Failed to extract and load JSON from text: {text}")
        return None

    def _format_serp(self, serp: dict) -> str:
        """格式化搜索结果"""
        serp_prompt = "\n".join(
            [
                f"<search results for '{query}'>\n"
                + "\n".join(
                    [
                        f"[web_{serp_no + 1}]\nweb title: {serp_i['title']}\nweb snippet: {serp_i.get('snippet', 'None')}"
                        for serp_no, serp_i in enumerate(serp[query])
                    ]
                )
                + f"\n</search results end>"
                for query in serp
            ]
        )
        return serp_prompt

    async def exec_step1(self, user_query):
        """生成关键词"""
        response = await self.model.query_one(
            messages=[
                {
                    "role": "user",
                    "content": self.step1_prompt.format(
                        user_query=user_query,
                        current_date=datetime.now().strftime("%Y-%m-%d"),
                    ),
                }
            ]
        )
        json_response = self._extract_and_load_json(response)
        logger.debug(f">>> STEP1 RESPONSE: {oneline_object(response)}")
        if not json_response:
            return {"status": "error", "message": "Failed to extract and load JSON from response"}
        if json_response["in_your_knowledge"]:
            return {"status": "in_knowledge"}
        else:
            return {"status": "not_in_knowledge", "queries": json_response["queries"]}

    async def exec_step2(self, queries, num_results=5):
        """执行搜索"""
        tasks = (self.search_tool_instance.search_google(query=query) for query in queries)
        search_results = await asyncio.gather(*tasks)
        serp = {
            query: search_result.get("organic", [])[:num_results]
            for query, search_result in zip(queries, search_results)
        }
        serp_prompt = self._format_serp(serp)
        logger.debug(f">>> QUERIES: {oneline_object(queries)}")
        logger.debug(f">>> SERP Prompt: {oneline_object(serp_prompt)}")

        response = await self.model.query_one(
            messages=[
                {
                    "role": "user",
                    "content": self.step2_prompt.format(
                        queries="\n".join(list(serp.keys())),
                        search_results=serp_prompt,
                        current_date=datetime.now().strftime("%Y-%m-%d"),
                    ),
                },
            ]
        )
        logger.debug(f">>> STEP2 RESPONSE: {oneline_object(response)}")
        return {"status": "success", "response": response}

    @async_file_cache(expire_time=None)
    async def generate_background_info(self, query, num_results=5) -> dict:
        """生成背景信息"""
        # 拆解关键词
        step1_result = await self.exec_step1(query)
        # 如果是已知知识，直接返回
        if step1_result["status"] == "in_knowledge":
            return {"status": "success", "background": ""}
        # 如果是未知知识，执行搜索
        else:
            step2_result = await self.exec_step2(step1_result["queries"], num_results)
            if step2_result["status"] == "error":
                return {"status": "error", "message": step2_result["message"]}
            else:
                # 返回搜索结果
                return {"status": "success", "background": step2_result["response"]}
