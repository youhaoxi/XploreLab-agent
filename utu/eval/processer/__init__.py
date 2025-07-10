from .base import BaseProcesser, BaseLLMJudgeProcesser, BaseMatchProcesser
from .gaia import GAIAProcesser
from .browse_comp import BrowseCompProcesser
from .browse_comp_zh import BrowseCompZHProcesser
from .xbench import XBenchProcesser
from .web_walker import WebWalkerProcesser
from ...utils import DIR_ROOT

from utu.config import EvalConfig


# factory class for evaluation
class ProcesserFactory:
    """
    Factory class for creating evaluation instances.
    """
    _registry = {}

    def __init__(self):
        # Register all processer classes
        self._recurse_register(BaseProcesser)
    
    def _recurse_register(self, cls: type[BaseProcesser]) -> None:
        """
        Recursively register all subclasses of cls.
        """
        for subcls in cls.__subclasses__():
            if hasattr(subcls, 'name') and subcls.name:
                self._registry[subcls.name] = subcls
                self._registry[subcls.name.lower()] = subcls
            # Recursively register subclasses
            self._recurse_register(subcls)
    
    @classmethod
    def get(cls, name: str, config: EvalConfig) -> BaseProcesser:
        """
        Get a processer class by name.
        """
        name_lower = name.lower()
        if name_lower not in cls._registry:
            # if the name is found, return the corresponding processer
            print(f"Processer for '{name}' not found. Using default processer.")
            return cls._registry["default"](config)
        return cls._registry[name_lower](config)
    
    @classmethod
    def get_all(cls) -> list[str]:
        """
        Get a list of all available processers.

        :return: A list of all available processers.
        """
        return list(cls._registry.keys())

    @classmethod
    def register(cls, name: str, processer_class: type[BaseProcesser]):
        """
        Register a processer class.

        :param name: The name of the processer.
        :param processer_class: The processer class to register.
        """
        if not issubclass(processer_class, BaseProcesser):
            raise TypeError(f"{processer_class} is not a subclass of BaseProcesser")
        cls._registry[name] = processer_class
        cls._registry[name.lower()] = processer_class


PROCESSER_FACTORY = ProcesserFactory()


BUILTIN_BENCHMARKS = {
    "GAIA_val": {
        "data_path": DIR_ROOT / "data" / "gaia" / "val.jsonl",
        "type": "single",
        "processer": "GAIA",
        "description": "GAIA validation set for evaluation"
    },
    "GAIA_test": {
        "data_path": DIR_ROOT / "data" / "gaia" / "test.jsonl",
        "type": "single",
        "processer": "GAIA",
        "description": "GAIA test set for evaluation"
    },
    "BrowseComp": {
        "data_path": DIR_ROOT / "data" / "browse_comp" / "test.jsonl",
        "type": "single",
        "processer": "BrowseComp",
        "description": "BrowseComp benchmark for evaluation"
    },
    "BrowseComp_ZH": {
        "data_path": DIR_ROOT / "data" / "browse_comp_zh" / "test.jsonl",
        "type": "single",
        "processer": "BrowseComp_ZH",
        "description": "BrowseComp Chinese benchmark for evaluation"
    },
    "XBench": {
        "data_path": DIR_ROOT / "data" / "xbench" / "test.jsonl",
        "type": "single",
        "processer": "XBench",
        "description": "XBench benchmark for evaluation"
    },
    "WebWalker": {
        "data_path": DIR_ROOT / "data" / "web_walker" / "test.jsonl",
        "type": "single",
        "processer": "WebWalker",
        "description": "WebWalker benchmark for evaluation"
    }
}
