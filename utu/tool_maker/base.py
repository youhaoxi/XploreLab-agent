from agents import Agent, function_tool
from agents.mcp import MCPServerStdioParams

from ..utils import oneline_object, get_logger

logger = get_logger(__name__)


@function_tool
def make_tool(task: str) -> MCPServerStdioParams:
    """Make a tool for the specified task

    Args:
        task (str): The task to make a tool for
    """
    logger.info(f"[tool] make_tool: {oneline_object(task)}")
    return MCPServerStdioParams(command="uvx", args=["mcp-server-time", "--local-timezone=Asia/Shanghai"])
