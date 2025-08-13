from agents.run import set_default_agent_runner

from .utils import assert_env
from .patch.runner import UTUAgentRunner

assert_env("UTU_LLM_TYPE")
print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
