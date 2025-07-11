import abc
from typing import Callable
from agents import FunctionTool, function_tool
import mcp.types as types

from utu.config import ToolkitConfig
from utu.utils import async_file_cache


class AsyncBaseToolkit(abc.ABC):
    config: ToolkitConfig
    tools_map: dict[str, Callable] = None

    # lifecycle
    async def __aenter__(self) -> "SearchToolkit": ...
    async def __aexit__(self, exc_type, exc_val, exc_tb): ...
    async def build(self): ...
    async def cleanup(self): ...

    # implementation
    @abc.abstractmethod
    async def get_tools_map(self) -> dict[str, Callable]: ...

    # utils
    async def get_tools_map_func(self) -> dict[str, Callable]: ...
    async def get_tools_in_agents(self) -> list[FunctionTool]: ...
    async def get_tools_in_openai(self) -> list[dict]: ...
    async def get_tools_in_mcp(self) -> list[types.Tool]: ...
    async def call_tool(self, name: str, arguments: dict) -> str: ...

class SearchToolkit(AsyncBaseToolkit):
    def __init__(self, config: ToolkitConfig = None):
        super().__init__(config)

    @async_file_cache(expire_time=None)
    async def search_google_api(self, query: str, num_results: int = 10) -> str:
        """Search the query via Google api, the query should be a search query like humans search in Google, concrete and not vague or super long. More the single most important items.
        
        Args:
            query (str): The query to search for.
            num_results (int, optional): The number of results to return. Defaults to 10.
        """
    @async_file_cache(expire_time=None)
    async def web_qa(self, url: str, query: str = None) -> str:
        """Query information you interested from the specified url
        
        Args:
            url (str): The url to get content from.
            query (str, optional): The query to search for. If not given, return the original content of the url.
        """

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "search_google_api": self.search_google_api,
            "web_qa": self.web_qa,
        }

TOOLKIT_MAP = {
    "search": SearchToolkit,
}

# usage
async def use_toolkit(config: ToolkitConfig):
    async with SearchToolkit(config) as toolkit:
        await toolkit.search_google_api("query", num_results=10)
