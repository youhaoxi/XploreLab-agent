from .base_env import BaseEnv
from .utils.docker_manager import DockerManager


class BrowserEnv(BaseEnv):
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.docker_manager = DockerManager()

    async def build(self):
        pass

    async def cleanup(self):
        pass

    def get_sp_prefix(self) -> str:
        return ""
