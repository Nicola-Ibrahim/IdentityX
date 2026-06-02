import importlib
import inspect
import os
import pkgutil
import sys
from typing import Any, Callable, TypeVar, get_args, get_origin

from src.building_blocks.application.mediator.messages.commands import BaseCommand, BaseCommandHandler
from src.building_blocks.application.mediator.messages.queries import BaseQuery, BaseQueryHandler
from src.building_blocks.application.mediator.core.behaviors import BaseBehavior
from src.building_blocks.application.mediator.core.exceptions import HandlerNotFoundError
from src.building_blocks.application.mediator.core.provider import ServiceContainer


class Mediator:
    """
    Lightweight, in-process CQRS Mediator.

    Responsibilities (strict 1-to-1):
      - ``execute(command)``  → dispatches a ``BaseCommand`` to its single handler.
      - ``query(query)``      → dispatches a ``BaseQuery`` to its single handler.

    Domain event dispatching (1-to-many) is intentionally **not** the
    Mediator's responsibility.  Use ``BaseEventBus`` / ``LocalEventBus`` for
    domain events.

    Pipeline behaviors (logging, validation, transactions) are applied around
    every command/query dispatch via the ``behaviors`` list.
    """

    def __init__(
        self,
        container: ServiceContainer | None = None,
        behaviors: list[BaseBehavior] | None = None,
    ) -> None:
        self._container = container
        self._registry: dict[type, type] = {}
        self._behaviors = behaviors or []
        self.auto_discover()

    def set_container(self, container: ServiceContainer) -> None:
        """Set the service container for dependency resolution."""
        self._container = container

    def auto_discover(self) -> None:
        """
        Scans all packages in the project, imports them to register subclasses,
        and builds the handler registry based on base class generics.
        Only ``BaseCommandHandler`` and ``BaseQueryHandler`` subclasses are
        discovered — notifications are handled by the EventBus.
        """
        search_path = sys.path[0] or os.getcwd()
        path = os.path.abspath(search_path)

        if path not in sys.path:
            sys.path.insert(0, path)

        ignore_dirs = {".git", ".venv", "venv", "__pycache__", "tests"}

        if os.path.isdir(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path) and item not in ignore_dirs:
                    try:
                        package = importlib.import_module(item)
                        pkg_path = getattr(package, "__path__", None)
                        if pkg_path:
                            for _, module_name, _ in pkgutil.walk_packages(pkg_path, package.__name__ + "."):
                                try:
                                    importlib.import_module(module_name)
                                except Exception:
                                    pass
                    except Exception:
                        pass

        # Register command and query handlers ONLY (not notifications)
        for handler_base in (BaseCommandHandler, BaseQueryHandler):
            self._register_subclasses(handler_base)

    def _register_subclasses(self, base_cls: type) -> None:
        def get_all_subclasses(cls):
            subclasses = []
            for subclass in cls.__subclasses__():
                subclasses.append(subclass)
                subclasses.extend(get_all_subclasses(subclass))
            return subclasses

        for handler_cls in get_all_subclasses(base_cls):
            if inspect.isabstract(handler_cls):
                continue

            request_type = self._extract_request_type(handler_cls)
            if request_type:
                self._registry[request_type] = handler_cls

    def _extract_request_type(self, handler_cls: type) -> type | None:
        for cls in handler_cls.__mro__:
            orig_bases = getattr(cls, "__orig_bases__", [])
            for base in orig_bases:
                origin = get_origin(base) or base
                if isinstance(origin, type) and issubclass(
                    origin, (BaseCommandHandler, BaseQueryHandler)
                ):
                    args = get_args(base)
                    if args:
                        req_type = args[0]
                        if not isinstance(req_type, TypeVar):
                            return req_type
        return None

    async def execute[TResponse](self, command: BaseCommand[TResponse]) -> TResponse:
        return await self._dispatch(command)

    async def query[TResponse](self, query: BaseQuery[TResponse]) -> TResponse:
        return await self._dispatch(query)

    async def _dispatch(self, request: Any) -> Any:
        handler_type = self._registry.get(type(request))
        if not handler_type:
            raise HandlerNotFoundError(f"No handler registered for request type: {type(request).__name__}")

        if self._container is None:
            raise RuntimeError(
                "Mediator: Service container is not set. Call set_container() or pass container during initialization."
            )

        handler = self._container.resolve(handler_type)

        async def core_handler() -> Any:
            return await handler.handle(request)

        pipeline = core_handler
        for behavior in reversed(self._behaviors):
            pipeline = self._wrap_behavior(behavior, request, pipeline)

        return await pipeline()

    def _wrap_behavior(self, behavior: BaseBehavior, request: Any, next_call: Callable[[], Any]) -> Callable[[], Any]:
        return lambda: behavior.handle(request, next_call)
