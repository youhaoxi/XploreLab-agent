from .base import UTUAgentBase
from .simple import UTUSimpleAgent
from .simple_env_agent import UTUSimpleEnvAgent
# from .tool_maker import UTUToolMakerAgent

from ..config import AgentConfig, ConfigLoader


AGENT_MAP = {
    "simple": UTUSimpleAgent,
    "simple_env": UTUSimpleEnvAgent,
}
def build_agent(config: AgentConfig|str, *args, **kwargs) -> UTUSimpleAgent|UTUSimpleEnvAgent:
    # a simple wrapper to load agent config and build agent
    if isinstance(config, str):
        config = ConfigLoader.load_agent_config(config)
    assert config.type in AGENT_MAP, f"Unknown agent type: {config.type}"
    return AGENT_MAP[config.type](config, *args, **kwargs)
