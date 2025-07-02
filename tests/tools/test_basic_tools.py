import pytest

from utu.config import ConfigLoader
from utu.tools import GitHubToolkit, ArxivToolkit, FileEditToolkit, WikipediaSearchTool


@pytest.fixture
def github_toolkit():
    return GitHubToolkit()

@pytest.fixture
def arxiv_toolkit():
    return ArxivToolkit()

@pytest.fixture
def file_edit_toolkit():
    return FileEditToolkit(config={
        "work_dir": "/tmp/",
        "backup_enabled": True,
        "default_encoding": "utf-8",
    })

@pytest.fixture
async def wikipedia_toolkit():
    return WikipediaSearchTool(config={
        "user_agent": "uTu-agent",
        "language": "en",
        "content_type": "text",
        "extract_format": "WIKI",
    })

async def test_get_repo_info(github_toolkit: GitHubToolkit):
    result = await github_toolkit.get_repo_info("https://github.com/github/github-mcp-server")
    assert result
    print(result)

async def test_search_papers(arxiv_toolkit: ArxivToolkit):
    result = await arxiv_toolkit.search_papers("tool maker")
    assert result
    print(result)

diff = """<<<<<<< SEARCH
line 1
=======
line 1 edited!
>>>>>>> REPLACE"""

async def test_edit_file(file_edit_toolkit: FileEditToolkit):
    result = await file_edit_toolkit.edit_file(
        "test.txt", 
        diff
    )
    print(result)

async def test_wikipedia_search(wikipedia_toolkit: WikipediaSearchTool):
    result = await wikipedia_toolkit.wikipedia_search("Python_(programming_language)")
    print(result)
    