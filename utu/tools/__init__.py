from .base import AsyncBaseToolkit
from .search import SearchToolkit
from ..config import ToolkitConfig

TOOLKIT_MAP = {
    "search": SearchToolkit,
}

def load_toolkit(toolkit_config: ToolkitConfig) -> AsyncBaseToolkit:
    if toolkit_config.mode == "builtin":
        assert toolkit_config.name in TOOLKIT_MAP, f"Unknown toolkit name: {toolkit_config.name}"
        return TOOLKIT_MAP[toolkit_config.name](
            config=toolkit_config,
            activated_tools=toolkit_config.activated_tools,
        )
    elif toolkit_config.mode == "mcp":
        raise NotImplementedError
    else:
        raise ValueError(f"Unknown toolkit mode: {toolkit_config.mode}")
