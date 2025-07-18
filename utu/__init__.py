# from agents import set_tracing_disabled
# set_tracing_disabled(True)


from .tracing import setup_phoenix_tracing
from .utils import setup_logging, setup_env


setup_env()
setup_logging()
setup_phoenix_tracing()
