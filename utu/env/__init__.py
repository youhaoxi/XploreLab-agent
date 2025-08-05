from .shell_local_env import ShellLocalEnv
from .base_env import BaseEnv, Env
from .browser_env import BrowserEnv
from ..utils import DIR_ROOT
from .utils.docker_manager import DockerManager
from .utils.mcp_client import MCPClient


async def get_env(env_name: str, trace_id: str) -> Env:
    if env_name == "base":
        return BaseEnv()
    elif env_name == "shell_local":
        workspace = DIR_ROOT / "workspace" / trace_id
        workspace.mkdir(parents=True, exist_ok=True)
        print(f"> Workspace: {workspace}")
        return ShellLocalEnv(workspace)
        # TODO: should setup tool.type == "env" -> handle in BaseAgent @eason
        # for toolkit in self._toolkits:
        #     if isinstance(toolkit, BashTool):
        #         toolkit.setup_workspace(self.env.workspace)
    elif env_name == "browser_docker":
        return BrowserEnv(trace_id)
    else:
        raise ValueError(f"Unknown env name: {env_name}")
