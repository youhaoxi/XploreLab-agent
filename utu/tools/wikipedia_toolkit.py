""" 
@smolagents/src/smolagents/default_tools.py
https://github.com/martin-majlis/Wikipedia-API
https://www.mediawiki.org/wiki/API:Main_page
"""
from typing import Callable

from .base import AsyncBaseToolkit
from ..config import ToolkitConfig


class WikipediaSearchTool(AsyncBaseToolkit):
    """
    WikipediaSearchTool searches Wikipedia and returns a summary or full text of the given topic, along with the page URL.

    Attributes:
        user_agent (str): A custom user-agent string to identify the project. This is required as per Wikipedia API policies, read more here: http://github.com/martin-majlis/Wikipedia-API/blob/master/README.rst
        language (str): The language in which to retrieve Wikipedia articles.
                http://meta.wikimedia.org/wiki/List_of_Wikipedias
        content_type (str): Defines the content to fetch. Can be "summary" for a short summary or "text" for the full article.
        extract_format (str): Defines the output format. Can be `"WIKI"` or `"HTML"`.
    """

    def __init__(self, config: ToolkitConfig|dict = None, activated_tools: list[str] = None) -> None:
        super().__init__(config, activated_tools)
        try:
            import wikipediaapi
        except ImportError as e:
            raise ImportError(
                "You must install `wikipedia-api` to run this tool: for instance run `pip install wikipedia-api`"
            ) from e

        # Map string format to wikipediaapi.ExtractFormat
        extract_format_map = {
            "WIKI": wikipediaapi.ExtractFormat.WIKI,
            "HTML": wikipediaapi.ExtractFormat.HTML,
        }
        self.user_agent = self.config.config.get("user_agent", "uTu-agent")
        self.language = self.config.config.get("language", "en")
        self.content_type = self.config.config.get("content_type", "text")
        extract_format = self.config.config.get("extract_format", "WIKI")
        if extract_format not in extract_format_map:
            raise ValueError("Invalid extract_format. Choose between 'WIKI' or 'HTML'.")
        self.extract_format = extract_format_map[extract_format]

        self.wiki = wikipediaapi.Wikipedia(
            user_agent=self.user_agent, language=self.language, extract_format=self.extract_format
        )

    async def wikipedia_search(self, query: str) -> str:
        """Searches Wikipedia and returns a summary or full text of the given topic, along with the page URL.
        
        Args:
            query (str): The topic to search on Wikipedia.
        """
        try:
            page = self.wiki.page(query)

            if not page.exists():
                return f"No Wikipedia page found for '{query}'. Try a different query."

            title = page.title
            url = page.fullurl

            if self.content_type == "summary":
                text = page.summary
            elif self.content_type == "text":
                text = page.text
            else:
                return "⚠️ Invalid `content_type`. Use either 'summary' or 'text'."

            return f"✅ **Wikipedia Page:** {title}\n\n**Content:** {text}\n\n🔗 **Read more:** {url}"

        except Exception as e:
            return f"Error fetching Wikipedia summary: {str(e)}"

    async def get_tools_map(self) -> dict[str, Callable]:
        return {
            "wikipedia_search": self.wikipedia_search,
        }
