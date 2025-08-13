from agents.run import set_default_agent_runner

from .patch.runner import UTUAgentRunner
from .utils import assert_env

assert_env("UTU_LLM_TYPE")
print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
