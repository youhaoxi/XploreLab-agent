# from agents import set_tracing_disabled
# set_tracing_disabled(True)

from dotenv import load_dotenv, find_dotenv

from .tracing import setup_phoenix_tracing
from .utils import setup_logging

load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)
setup_logging()
setup_phoenix_tracing()

from agents.run import set_default_agent_runner
from .patch.runner import UTUAgentRunner
print("patched runner!")
set_default_agent_runner(UTUAgentRunner())