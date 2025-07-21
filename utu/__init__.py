# from agents import set_tracing_disabled
# set_tracing_disabled(True)


from .tracing import setup_phoenix_tracing, setup_db_tracing
from .utils import setup_logging, setup_env


setup_env()
setup_logging()
setup_phoenix_tracing()
setup_db_tracing()

from agents.run import set_default_agent_runner
from .patch.runner import UTUAgentRunner
print("patched runner!")
set_default_agent_runner(UTUAgentRunner())
