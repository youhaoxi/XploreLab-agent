import pytest

from utu.tools.github_toolkit import GitHubToolkit
from utu.tools.arxiv_toolkit import ArxivToolkit
from utu.tools.file_edit_toolkit import FileEditToolkit


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
