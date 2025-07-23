# from agents import set_tracing_disabled
# set_tracing_disabled(True)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(raise_error_if_not_found=True), verbose=True, override=True)

from .tracing import setup_phoenix_tracing, setup_db_tracing
from .utils import setup_logging


setup_logging()
setup_phoenix_tracing()
setup_db_tracing()

from agents.run import set_default_agent_runner
from .patch.runner import UTUAgentRunner
print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
