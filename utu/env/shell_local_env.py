from .base_env import BaseEnv

SP_PREFIX = r"""<env>
{env}
</env>
<instructions>
1. You can only run bash commands in your workspace!!!
</instructions>
"""


class ShellLocalEnv(BaseEnv):
    workspace: str

    def __init__(self, workspace: str):
        self.workspace = workspace

    def get_sp_prefix(self) -> str:
        env_strs = [
            f"Time: {self.get_time()}",
            f"Workspace: {self.workspace}",
        ]
        sp_prefix = SP_PREFIX.format(env="\n".join(env_strs))
        return sp_prefix
