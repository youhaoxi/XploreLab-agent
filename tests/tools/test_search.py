import hashlib
import pytest

from utu.tools.search import SearchToolkit

test_url = "https://docs.crawl4ai.com/core/simple-crawling/"
test_query = "test"

@pytest.fixture
def search_toolkit():
    return SearchToolkit()

async def test_search_google_api(search_toolkit: SearchToolkit):
    result = await search_toolkit.search_google_api(test_query)
    assert result

async def test_get_content(search_toolkit: SearchToolkit):
    result = await search_toolkit.get_content(test_url)
    assert result

async def test_cache(search_toolkit: SearchToolkit):
    for i in range(2):
        res = await search_toolkit.get_content(test_url)
        hash = hashlib.md5(res.encode()).hexdigest()
        print(hash)
