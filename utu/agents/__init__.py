from .orchestra_agent import OrchestraAgent
from .simple_agent import SimpleAgent
from .base_agent import BaseAgent
from ..config import AgentConfig


def get_agent(config: AgentConfig) -> BaseAgent:
    if config.type == "simple":
        return SimpleAgent(config=config)
    elif config.type == "orchestra":
        return OrchestraAgent(config=config)
    else:
        raise ValueError(f"Unknown agent type: {config.type}")


__all__ = [
    "BaseAgent",
    "SimpleAgent",
    "OrchestraAgent",
    "get_agent",
]
