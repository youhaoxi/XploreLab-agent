import asyncio
import json
import os
import re
from typing import Callable

import requests

from ..config import ToolkitConfig
from ..utils import SimplifiedAsyncOpenAI, async_file_cache, get_logger, oneline_object
from .base import AsyncBaseToolkit

logger = get_logger(__name__)

""" ========== Decompose Query Toolkit ========= """
DECOMPOSE_QUERY_PROMPT = """As an expert research methodologist, your task is to decompose a complex research question into strategic sub-queries that will collectively build a comprehensive understanding of the topic.

<background>
{background}
</background>

Research Query: {query}

RESEARCH STRATEGY DEVELOPMENT:
1. First, identify the key dimensions of this topic (historical context, current developments, technical aspects, opposing viewpoints, practical applications, etc.)
2. For each dimension, formulate precise queries that will yield specific, actionable information
3. Consider both breadth (covering all relevant aspects) and depth (exploring critical details)
4. Include queries that may reveal contrasting perspectives or challenge dominant viewpoints

Generate {numSubQueries} strategic sub-queries that:
- Systematically address different conceptual dimensions of the main query
- Are precisely formulated to extract specific information
- Use optimal search syntax for maximum relevance (do not use operators like site:, filetype:, etc.)
- Include a mix of factual, analytical, and exploratory questions
- Cover both mainstream perspectives and potentially overlooked angles
- Address potential knowledge gaps or areas of uncertainty
- Follow a logical progression that builds comprehensive understanding

Format your response as JSON:
{{
  "subQueries": ["<query1>", "<query2>", "<query3>", ...],
}}"""


class DecomposeQueryToolkit(AsyncBaseToolkit):
    """解析 query 为 sub-query 的 toolkit"""

    def __init__(self, config: ToolkitConfig):
        super().__init__(config)
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_dump())
        self.num_sub_queries = self.config.config.get("num_sub_queries", 5)

    async def run(self, query: str, background: str = "") -> list[str]:
        """Decompose a query into sub-queries using an LLM.

        Args:
            query: The main query to decompose.
            background: Optional background information to provide context for decomposition.
        """
        prompt = DECOMPOSE_QUERY_PROMPT.format(query=query, background=background, numSubQueries=self.num_sub_queries)
        response = await self.llm.query_one(messages=[{"role": "user", "content": prompt}])
        # load json and extract subQueries from response string
        response = response.replace("```json", "").replace("```", "").strip()
        response_json = json.loads(response)
        return response_json.get("subQueries", [])

    async def get_tools_map(self) -> dict[str, Callable]:
        """Return a dictionary mapping tool names to tool functions."""
        return {"decompose_query": self.run}


""" ========== Web Search Toolkit ========= """
TEMPLATE_QA = r"""You are a webpage analysis agent that extract relevant information from the given webpage content to answer the given query. NOTE:
1. Be concise, do not extract too long or irrelevant information.
2. Before give your conclusion, you can summarize user's query if necessary.
3. Use language same as query.

<background>
{background}
</background>

<query>
{query}
</query>
<content>
{content}
</content>
"""
TEMPLATE_LINKS = r"""You are a webpage analysis agent that extract relevant links to the given query. NOTE:
1. You should extract the most relevant links to the query.
2. You can only output urls that exist in following webpage.
3. Output format: id.title(url)

<background>
{background}
</background>

<query>
{query}
</query>
<content>
{content}
</content>
"""

banned_sites = ("https://huggingface.co/datasets/", "https://grok.com/share/", "https://modelscope.cn/datasets/")
RE_MATCHED_SITES = re.compile(r"^(" + "|".join(banned_sites) + r")")


class WebSearchToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None):
        super().__init__(config)
        self.jina_url_template = r"https://r.jina.ai/{url}"
        self.jina_header = {"Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"}
        self.serper_url = r"https://google.serper.dev/search"
        self.serper_header = {"X-API-KEY": os.getenv("SERPER_API_KEY"), "Content-Type": "application/json"}
        # config
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_dump())
        self.num_result = self.config.config.get("num_result", 10)
        self.max_chars = self.config.config.get("max_chars", 300_000)
        self.max_concurrency = self.config.config.get("max_concurrency", 5)
        self.summary_token_limit = self.config.config.get("summary_token_limit", 1_000)

    async def run(self, query: str, background: str = "") -> list[dict]:
        """Search the query via Google api and get query-relevant information from each result. NOTE:
        1. try Google search operators, e.g. " " for exact match; -xxx for exclude; * wildcard matching; filetype:xxx for file types; site:xxx for site search. before:YYYY-MM-DD, after:YYYY-MM-DD for time range.
        2. search query should be concrete and not vague or super long

        Args:
            query (str): The query to search for.
        """
        # 1. search the query via Google api
        search_results = await self.search_google_api(query, self.num_result)
        # 2. get summary and links from each result
        # use asyncio.gather to run multiple tasks concurrently
        tasks = []
        for result in search_results:
            tasks.append(self.web_qa(result["link"], query, background))
        summaries = await asyncio.gather(*tasks)
        for i, result in enumerate(search_results):
            result["summary"] = summaries[i]
        return search_results

    @async_file_cache(expire_time=None)
    async def search_google(self, query: str):
        params = {"q": query, "gl": "cn", "hl": "zh-cn", "num": 100}
        response = requests.request("POST", self.serper_url, headers=self.serper_header, json=params)
        results = response.json()
        return results

    async def search_google_api(self, query: str, num_results: int = 10) -> list[dict]:
        """Search the query via Google api. NOTE:
        1. try Google search operators, e.g. " " for exact match; -xxx for exclude; * wildcard matching; filetype:xxx for file types; site:xxx for site search. before:YYYY-MM-DD, after:YYYY-MM-DD for time range.
        2. search query should be concrete and not vague or super long

        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 10.
        """
        # https://serper.dev/playground
        async with asyncio.Semaphore(self.max_concurrency):
            res = await self.search_google(query)
        # filter the search results
        results = self._filter_results(res["organic"], num_results)
        return results

    def _filter_results(self, results: list[dict], limit: int) -> list[dict]:
        # can also use search operator `-site:huggingface.co`
        res = []
        for result in results:
            if not RE_MATCHED_SITES.match(result["link"]):
                res.append(result)
            if len(res) >= limit:
                break
        return res

    @async_file_cache(expire_time=None)
    async def get_content(self, url: str) -> str:
        # Get the content of the url
        logger.info(f"[tool] get_content: {oneline_object(url)}")
        response = requests.get(self.jina_url_template.format(url=url), headers=self.jina_header)
        logger.info(f"[tool] get_content: {oneline_object(response.text)}...")
        return response.text

    # @async_file_cache(expire_time=None)
    async def web_qa(self, url: str, query: str = None, background: str = None) -> str:
        """Query information you interested from the specified url

        Args:
            url (str): The url to get content from.
            query (str, optional): The query to search for. If not given, return the original content of the url.
        """
        async with asyncio.Semaphore(self.max_concurrency):
            content = await self.get_content(url)
            query = query or "Summarize the content of this webpage."
            res_summary, res_links = await asyncio.gather(
                self._qa(content, query, background), self._extract_links(content, query, background)
            )
        result = f"Summary: {res_summary}\n\nRelated Links: {res_links}"
        return result

    async def _qa(self, content: str, query: str, background: str) -> str:
        content = content[: self.max_chars]  # truncate content to max_chars
        template = TEMPLATE_QA.format(content=content, query=query, background=background)
        return await self.llm.query_one(messages=[{"role": "user", "content": template}])

    async def _extract_links(self, content: str, query: str, background: str) -> str:
        content = content[: self.max_chars]  # truncate content to max_chars
        template = TEMPLATE_LINKS.format(content=content, query=query, background=background)
        return await self.llm.query_one(messages=[{"role": "user", "content": template}])

    async def get_tools_map(self) -> dict[str, Callable]:
        return {"web_search": self.run, "web_qa": self.web_qa, "search_google_api": self.search_google_api}


""" ========== Summarize Web Content Toolkit ========= """


class SummarizeToolkit(AsyncBaseToolkit):
    """Toolkit for summarizing web content based on search results."""

    def __init__(self, config: ToolkitConfig):
        super().__init__(config)
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_dump())
        self.max_chars = self.config.config.get("max_chars", 20_000)
        self.max_concurrency = self.config.config.get("max_concurrency", 5)

    async def run(self, query: str, background: str, search_results: list[dict]) -> str:
        """Summarize web content based on search results.

        Args:
            query (str): The original query that was used to perform the search.
            search_results (list[dict]): The list of search results to summarize.
        """
        formatted_search_result = self._get_formatted_search_result(search_results)
        prompt = SUMMARIZE_PROMPT.format(
            background=background, originalQuery=query, formattedSearchResults=formatted_search_result
        )

        async with asyncio.Semaphore(self.max_concurrency):
            # Use the LLM to generate the summary
            response = await self.llm.query_one(messages=[{"role": "user", "content": prompt}])
        return response.strip()

    def _get_formatted_search_result(self, search_results: list[dict]) -> str:
        """Format search results for the summarization prompt."""
        formatted_result = "<web_content>\n"
        for result_no, result in enumerate(search_results, start=1):
            try:
                formatted_result += (
                    f"<web_content_{result_no}>\n{result['summary'][: self.max_chars]}\n</web_content_{result_no}>\n"
                )
            except:
                pass
        formatted_result += "</web_content>"
        return formatted_result

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "summarize": self.run,
        }


SUMMARIZE_PROMPT = """You are an expert information synthesist tasked with creating precise, source-grounded summaries for specific question based on web search results. Your goal is to extract the most relevant information while maintaining traceability to original sources.

**Background**: {background}

**Question**: {originalQuery}

**Search Results**:
{formattedSearchResults}

**SUMMARY REQUIREMENTS**:
1. **Source-Driven Extraction**:
   - Extract only information explicitly stated in search results
   - Never add interpretations or inferences beyond source content
   - Identify key information using these priority filters:
     * Direct answers to question > Supporting context > Background details

2. **Conflict Handling**:
   - Clearly note contradictions between sources
   - Preserve differing viewpoints with source attribution
   - Never attempt to resolve conflicts through inference

3. **Information Structuring**:
   - Group related findings under thematic subheadings (max 3 levels)
   - Use bullet points for multi-source verification of same fact
   - Apply this information hierarchy:
     [Core Answer] → [Key Evidence] → [Supporting Context]

4. **Source Traceability**:
   - Embed numbered citations [1][2] after every factual claim
   - Include verbatim quotes for critical statements ("...") [3]
   - Maintain original source numbering from input

5. **Completeness Check**:
   - Ensure coverage of these dimensions:
     - Quantitative data (numbers, statistics)
     - Temporal references (time-sensitive info)
     - Entity relationships (who/what affects whom)
     - Consensus indicators (e.g., "most sources agree")

**PROHIBITED ACTIONS**:
- ❌ Generating conclusions not explicitly in sources
- ❌ Creating analogies or extended explanations
- ❌ Synthesizing new frameworks/theories
- ❌ Adding personal commentary

**OUTPUT FORMAT**:
### [Question Phrased as Header]
- Core finding summary (1-2 sentences)
- **Key Evidence**:
  - Fact with citation [1] 
  - Corroborating fact [2][3]
- **Contextual Notes**:
  - Temporal aspect: [date/relevance period] [4]
  - Conflict note: "Source [5] contradicts this, stating..."

**Quality Assurance**:
1. Every bullet must have ≥1 citation
2. Direct quotes must preserve original wording
3. Reject any source claiming "according to experts" without named experts
4. Flag inconclusive results: "No consensus on [aspect] ([1] vs [6])"""
