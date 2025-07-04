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


from ..config import ToolkitConfig, ConfigLoader

class ToolkitLoader:
    @classmethod
    def load_toolkits(cls, config: ToolkitConfig|str) -> AsyncBaseToolkit:
        if isinstance(config, str):
            config = ConfigLoader.load_toolkit_config(config)
        assert config.mode == "builtin", f"Unknown toolkit mode: {config.mode}"
        assert config.name in TOOLKIT_MAP, f"Unknown toolkit name: {config.name}"
        return TOOLKIT_MAP[config.name](config=config)