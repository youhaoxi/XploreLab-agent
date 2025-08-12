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
from .bash_remote_tool import BashRemoteToolkit
from .python_executor_tool import PythonExecutorTool
from .video_toolkit import VideoToolkit
from .audio_toolkit import AudioToolkit
from .serper_toolkit import SerperToolkit
from .ww_searcher_tools import DecomposeQueryToolkit, WebSearchToolkit, SummarizeToolkit


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
    "bash_remote": BashRemoteToolkit,
    "python_executor": PythonExecutorTool,
    "video": VideoToolkit,
    "audio": AudioToolkit,
    "serper": SerperToolkit,
    "query_decomposer": DecomposeQueryToolkit,
    "summarizer": SummarizeToolkit,
    "web_searcher": WebSearchToolkit,
}
