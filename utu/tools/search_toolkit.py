import os
import logging
import asyncio
from typing import Callable

import requests

from .base import AsyncBaseToolkit
from ..utils import oneline_object, async_file_cache, SimplifiedAsyncOpenAI, TokenUtils
from ..config import ToolkitConfig

logger = logging.getLogger("utu")


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
1. You should extract the most relevant links to the query.
2. You can only output urls that exist in following webpage.
3. Output format: id.title(url)

<query>
{query}
</query>
<content>
{content}
</content>
"""

class SearchToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None):
        super().__init__(config)
        self.jina_url_template = r"https://r.jina.ai/{url}"
        self.jina_header = {
            "Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"
        }
        self.serper_url = r"https://google.serper.dev/search"
        self.serper_header = {
            "X-API-KEY": os.getenv('SERPER_API_KEY'),
            'Content-Type': 'application/json'
        }
        # config
        self.llm = SimplifiedAsyncOpenAI(**self.config.config_llm.model_dump())
        self.summary_token_limit = self.config.config.get("summary_token_limit", 1_000)

    @async_file_cache(expire_time=None)
    async def search_google_api(self, query: str, num_results: int = 5) -> str:
        """Search the query via Google api, the query should be a search query like humans search in Google, concrete and not vague or super long. More the single most important items.
        
        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 5.
        """
        # https://serper.dev/playground
        logger.info(f"[tool] search_google_api: {oneline_object(query)}")
        params = {
            'q': query,
            'gl': 'cn',
            'hl': 'zh-cn',
            'num': num_results
        }
        response = requests.request("POST", self.serper_url, headers=self.serper_header, json=params)
        assert response.status_code == 200, response.text
        results = response.json()["organic"]
        msg = f'🔍  Results for query "{query}": {results}'
        logger.info(oneline_object(msg))
        return msg

    @async_file_cache(expire_time=None)
    async def get_content(self, url: str) -> str:
        # Get the content of the url
        logger.info(f"[tool] get_content: {oneline_object(url)}")
        response = requests.get(self.jina_url_template.format(url=url), headers=self.jina_header)
        logger.info(f"[tool] get_content: {oneline_object(response.text)}...")
        return response.text

    # @async_file_cache(expire_time=None)
    async def web_qa(self, url: str, query: str = None) -> str:
        """Query information you interested from the specified url
        
        Args:
            url (str): The url to get content from.
            query (str, optional): The query to search for. If not given, return the original content of the url.
        """
        logger.info(f"[tool] web_qa: {oneline_object({url, query})}")
        content = await self.get_content(url)
        query = query or "Summarize the content of this webpage."
        res_summary, res_links = await asyncio.gather(self._qa(content, query), self._extract_links(content, query))
        result = f"Summary: {res_summary}\n\nRelated Links: {res_links}"
        return result

    async def _qa(self, content: str, query: str) -> str:
        template = TEMPLATE_QA.format(content=content, query=query)
        return await self.llm.query_one(messages=[{"role": "user", "content": template}])
    async def _extract_links(self, content: str, query: str) -> str:
        template = TEMPLATE_LINKS.format(content=content, query=query)
        return await self.llm.query_one(messages=[{"role": "user", "content": template}])

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_google_api": self.search_google_api,
            # "get_content": self.get_content,
            "web_qa": self.web_qa,
        }
