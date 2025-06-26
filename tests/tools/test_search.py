import hashlib
import pytest

from utu.tools.search import SearchToolkit
from utu.utils import oneline_object
from utu.config import ConfigLoader, ToolkitConfig

@pytest.fixture
def config() -> ToolkitConfig: 
    config = ConfigLoader.load_toolkit_config("search")
    return config

@pytest.fixture
def search_toolkit(config: ToolkitConfig) -> SearchToolkit:
    return SearchToolkit(config=config)


test_query = "test"
async def test_search_google_api(search_toolkit: SearchToolkit):
    result = await search_toolkit.search_google_api(test_query)
    assert result

test_url = "https://docs.crawl4ai.com/core/simple-crawling/"
async def test_get_content(search_toolkit: SearchToolkit):
    result = await search_toolkit.get_content(test_url)
    assert result

async def test_cache(search_toolkit: SearchToolkit):
    for i in range(2):
        res = await search_toolkit.get_content(test_url)
        hash = hashlib.md5(res.encode()).hexdigest()
        print(hash)

queries = (
    ("https://docs.crawl4ai.com/core/simple-crawling/", ),
    ("https://docs.crawl4ai.com/core/simple-crawling/", "How to log?"),
    ("https://github.com/theskumar/python-dotenv", "Summary this page"),
)
async def test_web_qa(search_toolkit: SearchToolkit):
    for q in queries:
        print(f"query: {q}")
        result = await search_toolkit.web_qa(*q)
        print(f"result: {oneline_object(result)}")
