from .arxiv_toolkit import ArxivToolkit
from .audio_toolkit import AudioToolkit
from .base import AsyncBaseToolkit as AsyncBaseToolkit
from .bash_remote_tool import BashRemoteToolkit
from .bash_toolkit import BashToolkit
from .codesnip_toolkit import CodesnipToolkit
from .document_toolkit import DocumentToolkit
from .file_edit_toolkit import FileEditToolkit
from .github_toolkit import GitHubToolkit
from .image_toolkit import ImageToolkit
from .python_executor_toolkit import PythonExecutorToolkit
from .search_toolkit import SearchToolkit
from .serper_toolkit import SerperToolkit
from .video_toolkit import VideoToolkit
from .wikipedia_toolkit import WikipediaSearchTool

TOOLKIT_MAP = {
    "search": SearchToolkit,
    "document": DocumentToolkit,
    "image": ImageToolkit,
    "file_edit": FileEditToolkit,
    "github": GitHubToolkit,
    "arxiv": ArxivToolkit,
    "wikipedia": WikipediaSearchTool,
    "codesnip": CodesnipToolkit,
    "bash": BashToolkit,
    "bash_remote": BashRemoteToolkit,
    "python_executor": PythonExecutorToolkit,
    "video": VideoToolkit,
    "audio": AudioToolkit,
    "serper": SerperToolkit,
}
