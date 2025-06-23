import pytest

from utu.tools.search import SearchToolkit

@pytest.fixture
def search_toolkit():
    return SearchToolkit()


async def test_search_google_api(search_toolkit: SearchToolkit):
    result = await search_toolkit.search_google_api("test")
    assert result

async def test_get_content(search_toolkit: SearchToolkit):
    result = await search_toolkit.get_content("https://www.google.com")
    assert result
