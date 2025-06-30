from .base import BaseEval
from .gaia import GAIAEval
from .browse_comp import BrowseCompEval
from .browse_comp_zh import BrowseCompZHEval
from .xbench import XBenchEval

from utu.config import EvalConfig

# factory class for evaluation
class EvalFactory:
    """
    Factory class for creating evaluation instances.
    """
    _registry = {}

    def __init__(self):
        # Register all evaluation classes
        self._recurse_register(BaseEval)
    
    def _recurse_register(self, cls: type[BaseEval]) -> None:
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
    def get(cls, name: str, config: EvalConfig) -> BaseEval:
        """
        Get an evaluation instance by name.
        :param name: The name of the evaluation.
        :return: An instance of the evaluation class.
        """
        name_lower = name.lower()
        if name_lower not in cls._registry:
            # if the name is found, return the corresponding evaluation
            print(f"Evaluator for '{name}' not found. Using default evaluator.")
            return cls._registry["default"](config)
        # just for test
        if name_lower == "gaia":
            return cls._registry["browsecomp"](config)
        # just for test
        return cls._registry[name_lower](config)

    @classmethod
    def get_all(cls) -> list[str]:
        """
        Get a list of all available evaluations.
        :return: A list of all available evaluations.
        """
        return list(cls._registry.keys())

    @classmethod
    def register(cls, name: str, eval_class: type[BaseEval]):
        """
        Register a new evaluation class.
        :param name: The name of the evaluation.
        :param eval_class: The evaluation class to register.
        """
        if not issubclass(eval_class, BaseEval):
            raise TypeError(f"{eval_class} is not a subclass of BaseEval.")
        cls._registry[name] = eval_class

# Initialize the factory to register all evaluations
EVAL_FACTORY = EvalFactory()

from .mixed_evaluator import MixedEval
