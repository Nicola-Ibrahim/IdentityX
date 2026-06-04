from typing import Any, Callable, get_type_hints


class ServiceContainer:
    """
    A lightweight, built-in IoC container for the Mediator.
    Maps abstract interfaces to concrete factory callables.
    """

    def __init__(self) -> None:
        self._registry: dict[type, Callable[[], Any]] = {}

    def register(self, interface: type, factory: Callable[[], Any]) -> None:
        """Register a factory for an interface."""
        self._registry[interface] = factory

    def resolve(self, cls: type) -> Any:
        """
        Recursively resolve a class and all its __init__ dependencies
        by inspecting type hints. No third-party library needed.
        """
        if cls in self._registry:
            return self._registry[cls]()

        if hasattr(cls, "__init__"):
            hints = get_type_hints(cls.__init__)
            kwargs = {name: self.resolve(hint) for name, hint in hints.items() if name != "return"}
            return cls(**kwargs)

        raise LookupError(f"ServiceContainer: Cannot resolve {cls.__name__!r}")
