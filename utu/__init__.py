from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)

from agents.run import set_default_agent_runner
from .patch.runner import UTUAgentRunner

print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
