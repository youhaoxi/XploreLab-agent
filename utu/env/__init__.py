from .shell_local_env import ShellLocalEnv
from .base_env import BaseEnv, Env
from .browser_env import BrowserEnv
from ..utils import DIR_ROOT


async def get_env(env_name: str, trace_id: str) -> Env:
    if env_name == "base":
        return BaseEnv()
    elif env_name == "shell_local":
        workspace = DIR_ROOT / "workspace" / trace_id
        workspace.mkdir(parents=True, exist_ok=True)
        print(f"> Workspace: {workspace}")
        return ShellLocalEnv(workspace)
    elif env_name == "browser_docker":
        return BrowserEnv(trace_id)
    else:
        raise ValueError(f"Unknown env name: {env_name}")
