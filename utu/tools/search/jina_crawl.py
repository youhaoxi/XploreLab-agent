import aiohttp

from ...utils import EnvUtils, async_file_cache, get_logger

logger = get_logger(__name__)


class JinaCrawl:
    def __init__(self, config: dict = None) -> None:
        self.jina_url = "https://r.jina.ai/"
        self.jina_header = {
            "Authorization": f"Bearer {EnvUtils.get_env('JINA_API_KEY')}",
        }
        config = config or {}

    async def crawl(self, url: str) -> str:
        """standard crawl interface."""
        return await self.get_content(url)

    @async_file_cache(expire_time=None)
    async def get_content(self, url: str) -> str:
        # Get the content of the url
        params = {"url": url}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.jina_url, headers=self.jina_header, params=params) as response:
                text = await response.text()
                # logger.info(f"[tool] get_content: {oneline_object(text)}...")
                return text
