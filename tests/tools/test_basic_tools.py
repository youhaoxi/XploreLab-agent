import pytest

from utu.config import ConfigLoader
from utu.tools import (
    GitHubToolkit, ArxivToolkit, FileEditToolkit, WikipediaSearchTool, 
    CodesnipToolkit, BashTool, BashRemoteToolkit, PythonExecuteTool,
)


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

async def test_wikipedia_revisions(wikipedia_toolkit: WikipediaSearchTool):
    result = await wikipedia_toolkit.search_wikipedia_revisions("Penguin", 2022, 12)
    print(result)

@pytest.fixture
def codesnip_toolkit() -> CodesnipToolkit:
    config = ConfigLoader.load_toolkit_config("codesnip")
    return CodesnipToolkit(config=config)

async def test_run_code(codesnip_toolkit: CodesnipToolkit):
    result = await codesnip_toolkit.run_code("print('hello world')", "python")
    print(result)

@pytest.fixture
def bash_toolkit() -> BashTool:
    config = ConfigLoader.load_toolkit_config("bash")
    return BashTool(config=config)

async def test_run_bash(bash_toolkit: BashTool):
    result = await bash_toolkit.run_bash("curl https://httpbin.org/get")
    print(result)
    result = await bash_toolkit.run_bash("wget https://www.gnu.org/software/wget/manual/wget.html -O wget.html")
    print(result)

@pytest.fixture
def bash_remote_toolkit() -> BashRemoteToolkit:
    config = ConfigLoader.load_toolkit_config("bash_remote")
    return BashRemoteToolkit(config=config)

async def test_remote_bash(bash_remote_toolkit: BashRemoteToolkit):
    await bash_remote_toolkit.build()
    # "curl https://httpbin.org/get"
    cmd = "pwd"
    result = await bash_remote_toolkit.exec(cmd)
    print(result)
    await bash_remote_toolkit.cleanup()

@pytest.fixture
def python_execute_toolkit() -> PythonExecuteTool:
    return PythonExecuteTool()

async def test_python_execute(python_execute_toolkit: PythonExecuteTool):
    test_code = """
import numpy as np
a = 1
a
"""
    result = await python_execute_toolkit.execute_python_code(code=test_code)
    print(result)
    assert result["success"]
    assert "1" in result["output"]

    test_code_with_plot = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', label='sin(x)')
plt.title('Sine Function')
plt.grid(True)

print("Image generated")
"""
    result_plot = await python_execute_toolkit.execute_python_code(code=test_code_with_plot, workdir="./test_output")
    print(result_plot)
    assert result_plot['success']
    assert "Image generated" in result_plot['output']
    assert len(result_plot['files']) == 1
    assert "output_image.png" in result_plot['files'][0]
