import datetime

from .simple import UTUSimpleAgent
from ..config import AgentConfig
from ..utils import DIR_ROOT
from ..tools import BashTool


class Env:
    workspace: str

    def __init__(self, workspace: str):
        self.workspace = workspace

    @staticmethod
    def get_time() -> str:
        return datetime.datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")


SP_PREFIX = r"""<env>
{env}
</env>
<instructions>
1. You can only run bash commands in your workspace!!!
</instructions>
"""

class UTUSimpleEnvAgent(UTUSimpleAgent):
    """SimpleAgent with environment
    ugly implementation now!!!
    TODO: seperate Env class @eason
    """

    def __init__(self, config: AgentConfig|str, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self._setup_env()

    def _setup_env(self):
        workspace = DIR_ROOT / "workspace" / self.trace_id
        workspace.mkdir(parents=True, exist_ok=True)
        print(f"> Workspace: {workspace}")
        self.env = Env(workspace=workspace)

    async def build_instructions(self) -> str:
        env_strs = [
            f"Time: {Env.get_time()}",
            f"Workspace: {self.env.workspace}",
        ]
        sp_prefix = SP_PREFIX.format(env="\n".join(env_strs))
        return sp_prefix + await super().build_instructions()

    async def build(self):
        await super().build()
        # TODO: should setup tool.type == "env" -> handle in BaseAgent @eason
        for toolkit in self._toolkits:
            if isinstance(toolkit, BashTool):
                toolkit.setup_workspace(self.env.workspace)
