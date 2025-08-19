import hashlib
import json

import pytest

from utu.config import ConfigLoader
from utu.tools import SearchToolkit


@pytest.fixture
def search_toolkit() -> SearchToolkit:
    config = ConfigLoader.load_toolkit_config("search")
    return SearchToolkit(config=config)


async def test_tool_schema(search_toolkit: SearchToolkit):
    tools = await search_toolkit.get_tools_in_agents()
    for tool in tools:
        print(f"{tool.name}: {tool.description}")
        print(json.dumps(tool.params_json_schema, indent=2, ensure_ascii=False))


# test filter of huggingface.co
# TEST_QUERY = "Illuvium Zero testnet launch date iOS Google Play"
TEST_QUERY = "南京工业大学计算机与信息工程学院 更名 报道"


async def test_search_google_api(search_toolkit: SearchToolkit):
    result = await search_toolkit.search_google_api(TEST_QUERY, num_results=10)
    print(result)


TEST_URL = "https://docs.crawl4ai.com/core/simple-crawling/"


async def test_get_content(search_toolkit: SearchToolkit):
    result = await search_toolkit.get_content(TEST_URL)
    print(result)


async def test_cache(search_toolkit: SearchToolkit):
    for _ in range(2):
        res = await search_toolkit.get_content(TEST_URL)
        hash = hashlib.md5(res.encode()).hexdigest()
        print(hash)


queries = (
    ("https://docs.crawl4ai.com/core/simple-crawling/", ""),
    ("https://docs.crawl4ai.com/core/simple-crawling/", "How to log?"),
    ("https://github.com/theskumar/python-dotenv", "Summary this page"),
)


async def test_web_qa(search_toolkit: SearchToolkit):
    for q in queries:
        print(f"query: {q}")
        result = await search_toolkit.web_qa(*q)
        print(f"result: {result}")
