import os
import logging
from typing import Callable

import requests

from .base import AsyncBaseToolkit
from ..utils import oneline_object, async_file_cache, SimplifiedAsyncOpenAI, TokenUtils
from ..config import ToolkitConfig

logger = logging.getLogger("utu")


# TODO: ref @smolagents -- to keep rich context info
TEMPLATE_SUMMARY = r"""请对于以下内容进行总结：
<content>
{content}
</content>

输出格式: Markdown"""

TEMPLATE_QA = r"""请根据下面的 <content> 内容回答 <query>:
<query>
{query}
</query>
<content>
{content}
</content>
"""

class SearchToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None, activated_tools: list[str] = None):
        super().__init__(config, activated_tools)
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
        llm_config = self.config.get("llm", {})
        self.llm = SimplifiedAsyncOpenAI(**llm_config)
        self.summary_token_limit = self.config.get("summary_token_limit", 10_000)

    @async_file_cache(expire_time=None)
    async def search_google_api(self, query: str, num_results: int = 20) -> str:
        """Search the query via Google api, the query should be a search query like humans search in Google, concrete and not vague or super long. More the single most important items.
        
        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 20.
        """
        logger.info(f"[tool] search_google_api: {oneline_object(query)}")
        params = {
            'q': query,
            'gl': 'cn',
            'hl': 'zh-cn',
            'num_results': num_results
        }
        response = requests.request("POST", self.serper_url, headers=self.serper_header, json=params)
        results = response.json()["organic"]
        msg = f'🔍  Results for query "{query}": {results}'
        logger.info(oneline_object(msg))
        return msg

    @async_file_cache(expire_time=None)
    async def get_content(self, url: str) -> str:
        """Get the content of the url
        
        Args:
            url (str): The url to get content from.
        """
        logger.info(f"[tool] get_content: {oneline_object(url)}")
        response = requests.get(self.jina_url_template.format(url=url), headers=self.jina_header)
        logger.info(f"[tool] get_content: {oneline_object(response.text)}...")
        return response.text

    @async_file_cache(expire_time=None)
    async def web_qa(self, url: str, query: str = None) -> str:
        """Query information you interested from the specified url
        
        Args:
            url (str): The url to get content from.
            query (str, optional): The query to search for. If not given, return the original content of the url.
        """
        logger.info(f"[tool] web_qa: {oneline_object({url, query})}")
        raw_content = await self.get_content(url)
        if query is None:
            result = await self._summary(raw_content)
        else:
            result = await self._qa(raw_content, query)
        return result

    async def _summary(self, content: str) -> str:
        if TokenUtils.count_tokens(content) > self.summary_token_limit:
            template = TEMPLATE_SUMMARY.format(content=content)
            summarized_content = await self.llm.query_one(messages=[{"role": "user", "content": template}])
            if "Markdown Content" in content:
                header = content.split("Markdown Content")[0]
            else:
                header = ""
            content = f"{header}Summaried Content (The original content is too long to show here.)\n{summarized_content}"
        return content

    async def _qa(self, content: str, query: str) -> str:
        template = TEMPLATE_QA.format(content=content, query=query)
        return await self.llm.query_one(messages=[{"role": "user", "content": template}])

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_google_api": self.search_google_api,
            "get_content": self.get_content,
        }
