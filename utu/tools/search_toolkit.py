import asyncio
import re
from typing import Callable

import aiohttp

from ..config import ToolkitConfig
from ..utils import SimplifiedAsyncOpenAI, async_file_cache, get_logger, oneline_object
from .base import AsyncBaseToolkit

logger = get_logger(__name__)


# TODO: ref @smolagents -- to keep rich context info
TEMPLATE_QA = r"""You are a webpage analysis agent that extract relevant information from the given webpage content to answer the given query. NOTE:
1. Be concise, do not extract too long or irrelevant information.
2. Before give your conclusion, you can summarize user's query if necessary.
3. Use language same as query.

<query>
{query}
</query>
<content>
{content}
</content>
"""
TEMPLATE_LINKS = r"""You are a webpage analysis agent that extract relevant links to the given query. NOTE:
1. You should extract the most relevant links to the query. Do not include the url of given webpage.
2. You can only output urls that exist in following webpage.
3. Output format: id. title(url)

<query>
{query}
</query>
<content>
{content}
</content>
"""

banned_sites = ("https://huggingface.co/datasets/", "https://grok.com/share/", "https://modelscope.cn/datasets/")
RE_MATCHED_SITES = re.compile(r"^(" + "|".join(banned_sites) + r")")


class SearchToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None):
        super().__init__(config)
        self.jina_url_template = r"https://r.jina.ai/{url}"
        self.jina_header = {"Authorization": f"Bearer {self.config.config.get('JINA_API_KEY')}"}
        self.serper_url = r"https://google.serper.dev/search"
        self.serper_header = {"X-API-KEY": self.config.config.get("SERPER_API_KEY"), "Content-Type": "application/json"}
        # config
        self.llm = SimplifiedAsyncOpenAI(
            **self.config.config_llm.model_provider.model_dump() if self.config.config_llm else {}
        )
        self.summary_token_limit = self.config.config.get("summary_token_limit", 1_000)

    @async_file_cache(expire_time=None)
    async def search_google(self, query: str):
        params = {"q": query, "gl": "cn", "hl": "zh-cn", "num": 100}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.serper_url, headers=self.serper_header, json=params) as response:
                response.raise_for_status()  # avoid cache error!
                results = await response.json()
                return results

    async def search_google_api(self, query: str, num_results: int = 5) -> dict:
        """web search to gather information from the web.

        Tips:
        1. search query should be concrete and not vague or super long
        2. try to add Google search operators in query if necessary,
        - " " for exact match;
        - -xxx for exclude;
        - * wildcard matching;
        - filetype:xxx for file types;
        - site:xxx for site search;
        - before:YYYY-MM-DD, after:YYYY-MM-DD for time range.

        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 5.
        """
        # https://serper.dev/playground
        logger.info(f"[tool] search_google_api: {oneline_object(query)}")
        res = await self.search_google(query)
        # filter the search results
        results = self._filter_results(res["organic"], num_results)
        formatted_results = []
        for i, r in enumerate(results, 1):
            formatted_results.append(f"{i}. {r['title']} ({r['link']})")
            if "snippet" in r:
                formatted_results[-1] += f"\nsnippet: {r['snippet']}"
            if "sitelinks" in r:
                formatted_results[-1] += f"\nsitelinks: {r['sitelinks']}"
        msg = "\n".join(formatted_results)
        logger.info(oneline_object(msg))
        return msg

    def _filter_results(self, results: list[dict], limit: int) -> list[dict]:
        # can also use search operator `-site:huggingface.co`
        # ret: {title, link, snippet, position, | sitelinks}
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
        async with aiohttp.ClientSession() as session:
            async with session.get(self.jina_url_template.format(url=url), headers=self.jina_header) as response:
                text = await response.text()
                logger.info(f"[tool] get_content: {oneline_object(text)}...")
                return text

    # @async_file_cache(expire_time=None)
    async def web_qa(self, url: str, query: str = None) -> str:
        """Ask question to a webpage, you will get the answer and related links from the specified url.

        Args:
            url (str): The url to ask question to.
            query (str, optional): The question to ask. If not given, return the summary of the webpage.
        """
        logger.info(f"[tool] web_qa: {oneline_object({url, query})}")
        content = await self.get_content(url)
        query = (
            query or "Summarize the content of this webpage, in the same language as the webpage."
        )  # use the same language
        res_summary, res_links = await asyncio.gather(self._qa(content, query), self._extract_links(content, query))
        result = f"Summary: {res_summary}\n\nRelated Links: {res_links}"
        return result

    async def _qa(self, content: str, query: str) -> str:
        template = TEMPLATE_QA.format(content=content, query=query)
        return await self.llm.query_one(
            messages=[{"role": "user", "content": template}], **self.config.config_llm.model_params.model_dump()
        )

    async def _extract_links(self, content: str, query: str) -> str:
        template = TEMPLATE_LINKS.format(content=content, query=query)
        return await self.llm.query_one(
            messages=[{"role": "user", "content": template}], **self.config.config_llm.model_params.model_dump()
        )

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_google_api": self.search_google_api,
            # "get_content": self.get_content,
            "web_qa": self.web_qa,
        }
