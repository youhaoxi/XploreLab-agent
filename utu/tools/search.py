import os
from typing import Callable

import requests

from .base import AsyncBaseToolkit
from ..utils import logger


class SearchToolkit(AsyncBaseToolkit):
    def __init__(self):
        self.jina_url_template = r"https://r.jina.ai/{url}"
        self.jina_header = {
            "Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"
        }
        self.serper_url = r"https://google.serper.dev/search"
        self.serper_header = {
            "X-API-KEY": os.getenv('SERPER_API_KEY'),
            'Content-Type': 'application/json'
        }

    async def search_google_api(self, query: str, num_results: int = 20) -> str:
        """Search the query via Google api, the query should be a search query like humans search in Google, concrete and not vague or super long. More the single most important items.
        
        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 20.
        """
        logger.info(f"[tool] search_google_api: {query}")
        params = {
            'q': query,
            'gl': 'cn',
            'hl': 'zh-cn',
            'num_results': num_results
        }
        response = requests.request("POST", self.serper_url, headers=self.serper_header, json=params)
        results = response.json()["organic"]
        msg = f'🔍  Results for query "{query}": {results}'
        logger.info(msg)
        return msg

    async def get_content(self, url: str) -> str:
        """Get the content of the url
        
        Args:
            url (str): The url to get content from.
        """
        logger.info(f"[tool] get_content: {url}")
        response = requests.get(self.jina_url_template.format(url=url), headers=self.jina_header)
        logger.info(f"[tool] get_content: {response.text[:100]}...")
        return response.text
        

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_google_api": self.search_google_api,
            "get_content": self.get_content,
        }
