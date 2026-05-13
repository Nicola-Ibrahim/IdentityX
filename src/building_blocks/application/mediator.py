import importlib
import inspect
import pkgutil
from typing import Any, Callable, TypeVar, get_type_hints

from .commands import BaseCommand
from .queries import BaseQuery

TResponse = TypeVar("TResponse")


class MediatorError(Exception):
    """Base exception for mediator errors."""

    pass


class HandlerNotFoundError(MediatorError):
    """Raised when no handler is found for a request."""

    pass


class HandlerRegistry:
    """Internal registry for mapping requests to their handlers."""

    def __init__(self):
        self._handlers: dict[type, type] = {}

    def register(self, request_type: type, handler_type: type):
        self._handlers[request_type] = handler_type

    def get(self, request_type: type) -> type | None:
        return self._handlers.get(request_type)


# Singleton registry for global discovery
_global_registry = HandlerRegistry()


class Mediator:
    """
    A lightweight, enterprise-grade Mediator inspired by MediatR (C#).
    Encapsulates request/response patterns and cross-cutting concerns via pipelines.
    """

    def __init__(self, service_provider: Callable[[type], Any], behaviors: list[Any] | None = None) -> None:
        """
        :param service_provider: Callable to resolve dependencies from a DI container.
        :param behaviors: List of pipeline behaviors to wrap execution.
        """
        self._service_provider = service_provider
        self._behaviors = behaviors or []

    @staticmethod
    def scan(root_package: str) -> None:
        """
        Automatically discovers and registers all handlers in the specified package.
        """
        # 1. Recursive module discovery
        pkg = importlib.import_module(root_package)
        for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix=root_package + "."):
            try:
                importlib.import_module(name)
            except Exception:
                continue

        # 2. Handler registration via type hint inspection
        from .commands import BaseCommandHandler
        from .queries import BaseQueryHandler

        for base_cls, arg_name in [(BaseCommandHandler, "command"), (BaseQueryHandler, "query")]:
            for subclass in Mediator._get_all_subclasses(base_cls):
                if inspect.isabstract(subclass):
                    continue

                try:
                    hints = get_type_hints(subclass.handle)
                    req_type = hints.get(arg_name)
                    if req_type and req_type is not inspect.Parameter.empty:
                        _global_registry.register(req_type, subclass)
                except (TypeError, NameError):
                    # Skip classes with unresolved type hints
                    continue

    async def execute(self, command: BaseCommand[TResponse]) -> TResponse:
        """Execute a command through the mediator pipeline."""
        return await self._dispatch(command)

    async def query(self, query: BaseQuery[TResponse]) -> TResponse:
        """Execute a query through the mediator pipeline."""
        return await self._dispatch(query)

    async def _dispatch(self, request: Any) -> Any:
        handler_type = _global_registry.get(type(request))
        if not handler_type:
            raise HandlerNotFoundError(f"No handler registered for request type: {type(request).__name__}")

        # Resolve handler instance from service provider (DI Container)
        handler = self._service_provider(handler_type)

        # Core execution logic
        async def core_handler():
            return await handler.handle(request)

        # Build execution pipeline from behaviors
        pipeline = core_handler
        for behavior in reversed(self._behaviors):
            pipeline = self._wrap_behavior(behavior, request, pipeline)

        return await pipeline()

    def _wrap_behavior(self, behavior: Any, request: Any, next_call: Callable) -> Callable:
        """Wraps a behavior around the next step in the pipeline."""
        return lambda: behavior.handle(request, next_call)

    @staticmethod
    def _get_all_subclasses(cls: type) -> set[type]:
        """Recursively finds all subclasses of a given class."""
        subclasses = set(cls.__subclasses__())
        return subclasses.union([s for c in subclasses for s in Mediator._get_all_subclasses(c)])
