import pytest

from utu.tools.github import GitHubToolkit
from utu.tools.arxiv import ArxivToolkit

@pytest.fixture
def github_toolkit():
    return GitHubToolkit()

@pytest.fixture
def arxiv_toolkit():
    return ArxivToolkit()

async def test_get_repo_info(github_toolkit: GitHubToolkit):
    result = await github_toolkit.get_repo_info("https://github.com/github/github-mcp-server")
    assert result
    print(result)

async def test_search_papers(arxiv_toolkit: ArxivToolkit):
    result = await arxiv_toolkit.search_papers("tool maker")
    assert result
    print(result)
