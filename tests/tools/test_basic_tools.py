import pytest

from utu.tools.github import GitHubToolkit

@pytest.fixture
def github_toolkit():
    return GitHubToolkit()

async def test_get_repo_info(github_toolkit: GitHubToolkit):
    result = await github_toolkit.get_repo_info("https://github.com/github/github-mcp-server")
    assert result
    print(result)