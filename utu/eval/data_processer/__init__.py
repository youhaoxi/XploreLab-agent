from .base import BaseProcesser

from utu.config import EvalConfig

# factory class for data processer
class DataProcesserFactory:
    """
    Factory class to create data processer instances.
    """
    _registry = {}
    
    def __init__(self):
        # Register all evaluation classes
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
        Get a data processer instance by name.
        :param name: The name of the data processer.
        :return: An instance of the data processer class.
        """
        name_lower = name.lower()
        if name_lower not in cls._registry:
            print(f"Data processer '{name}' not found. Using default processer.")
            return cls._registry["default"](config)
        return cls._registry[name_lower](config)

    @classmethod
    def get_all(cls) -> list[str]:
        """
        Get a list of all available data processers.
        :return: A list of all available data processers.
        """
        return list(cls._registry.keys())
    
    @classmethod
    def register(cls, name: str, processer_class: type[BaseProcesser]):
        """
        Register a new data processer class.
        :param name: The name of the data processer.
        :param processer_class: The data processer class to register.
        """
        if not issubclass(processer_class, BaseProcesser):
            raise TypeError(f"{processer_class} is not a subclass of BaseProcesser.")
        cls._registry[name] = processer_class


# Initialize the factory to register all data processers
DATA_PROCESSER_FACTORY = DataProcesserFactory()

from .mixed_processer import MixedProcesser
