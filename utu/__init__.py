# ruff: noqa
from agents.run import set_default_agent_runner

from .utils import EnvUtils
from .patch.runner import UTUAgentRunner

EnvUtils.assert_env("UTU_LLM_TYPE")
# print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
