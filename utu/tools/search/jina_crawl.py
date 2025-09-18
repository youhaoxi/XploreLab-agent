import aiohttp

from ...utils import EnvUtils, async_file_cache, get_logger

logger = get_logger(__name__)


class JinaCrawl:
    def __init__(self, config: dict = None) -> None:
        self.jina_url = "https://r.jina.ai/"
        self.jina_header = {}
        api_key = EnvUtils.get_env("JINA_API_KEY", "")
        if api_key:
            self.jina_header["Authorization"] = f"Bearer {api_key}"
        else:
            # https://jina.ai/api-dashboard/rate-limit
            logger.warning("Jina API key not found! Access rate may be limited.")
        for k, v in config.get("crawl_params", {}).items():
            self.jina_header[k] = v

    async def crawl(self, url: str) -> str:
        """standard crawl interface."""
        return await self.crawl_jina(url)

    @async_file_cache(expire_time=None)
    async def crawl_jina(self, url: str) -> str:
        # Get the content of the url
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.jina_url}/{url}", headers=self.jina_header) as response:
                response.raise_for_status()  # avoid cache error!
                text = await response.text()
                return text
