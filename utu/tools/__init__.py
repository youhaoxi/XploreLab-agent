from .base import AsyncBaseToolkit
from .search_toolkit import SearchToolkit
from .document_toolkit import DocumentToolkit
from .image_toolkit import ImageToolkit
from .file_edit_toolkit import FileEditToolkit
from .github_toolkit import GitHubToolkit
from .arxiv_toolkit import ArxivToolkit
from .wikipedia_toolkit import WikipediaSearchTool
from .codesnip_toolkit import CodesnipToolkit
from .bash_tool import BashTool


TOOLKIT_MAP = {
    "search": SearchToolkit,
    "document": DocumentToolkit,
    "image": ImageToolkit,
    "file_edit": FileEditToolkit,
    "github": GitHubToolkit,
    "arxiv": ArxivToolkit,
    "wikipedia": WikipediaSearchTool,
    "codesnip": CodesnipToolkit,
    "bash": BashTool,
}
