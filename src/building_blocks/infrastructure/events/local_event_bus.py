import importlib
import inspect
import os
import pkgutil
import sys
from typing import Any, TypeVar, get_args, get_origin

from src.building_blocks.application.events.base_event_bus import BaseEventBus
from src.building_blocks.application.events.base_event_handler import BaseEventHandler
from src.building_blocks.domain.events import DomainEvent


class LocalEventBus(BaseEventBus):
    """
    In-memory, synchronous 1-to-many event bus.

    On construction it scans the project for every concrete ``BaseEventHandler``
    subclass, inspects its generic type parameter to determine which event type
    it handles, and builds an internal registry — exactly the same auto-discovery
    strategy used by the ``Mediator`` for commands and queries.

    Handlers are executed **sequentially** so that a shared ``AsyncSession``
    (from SQLAlchemy) is safe to use inside handlers without concurrency issues.

    Replacing with a real broker
    ----------------------------
    To move to RabbitMQ, Redis Pub/Sub, or any other transport, implement
    ``BaseEventBus`` in ``infrastructure/events/`` and change only the binding
    in ``startup.py``::

        event_bus = BrokerEventBus(connection_url=settings.AMQP_URL)

    No domain, repository, or handler code changes.
    """

    def __init__(self, container: Any) -> None:
        """
        Parameters
        ----------
        container:
            A ``ServiceContainer`` (or any object with a ``resolve(cls)`` method)
            used to instantiate handlers with their dependencies.
        """
        self._container = container
        # Maps event type → list of handler classes that process it
        self._registry: dict[type, list[type]] = {}
        self._auto_discover()

    # ---------------------------------------------------------------------- #
    # Auto-discovery
    # ---------------------------------------------------------------------- #

    def _auto_discover(self) -> None:
        """
        Walk all packages under ``sys.path[0]`` (the project root) and import
        every Python module so that ``BaseEventHandler`` subclasses are defined
        and can be discovered via ``__subclasses__()``.
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
                            for _, module_name, _ in pkgutil.walk_packages(
                                pkg_path, package.__name__ + "."
                            ):
                                try:
                                    importlib.import_module(module_name)
                                except Exception:
                                    pass
                    except Exception:
                        pass

        self._register_handlers(BaseEventHandler)

    def _register_handlers(self, base_cls: type) -> None:
        """Recursively collect concrete handler subclasses and build the registry."""

        def all_subclasses(cls: type) -> list[type]:
            result = []
            for sub in cls.__subclasses__():
                result.append(sub)
                result.extend(all_subclasses(sub))
            return result

        for handler_cls in all_subclasses(base_cls):
            if inspect.isabstract(handler_cls):
                continue

            event_type = self._extract_event_type(handler_cls)
            if event_type is None:
                continue

            if event_type not in self._registry:
                self._registry[event_type] = []
            if handler_cls not in self._registry[event_type]:
                self._registry[event_type].append(handler_cls)

    def _extract_event_type(self, handler_cls: type) -> type | None:
        """
        Inspect the MRO of ``handler_cls`` to find the concrete event type
        bound to the ``BaseEventHandler[TEvent]`` generic parameter.
        """
        for cls in handler_cls.__mro__:
            for base in getattr(cls, "__orig_bases__", []):
                origin = get_origin(base) or base
                if isinstance(origin, type) and issubclass(origin, BaseEventHandler):
                    args = get_args(base)
                    if args:
                        candidate = args[0]
                        # Exclude unresolved TypeVars
                        if not isinstance(candidate, TypeVar):
                            return candidate
        return None

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    async def publish(self, event: DomainEvent) -> None:
        """
        Dispatch ``event`` to every registered handler for its type.

        Handlers are called sequentially.  If a handler raises, publishing
        stops immediately (fail-fast).
        """
        handler_classes = self._registry.get(type(event), [])
        for handler_cls in handler_classes:
            handler = self._container.resolve(handler_cls)
            await handler.handle(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        """Publish multiple events in order, delegating each to ``publish()``."""
        for event in events:
            await self.publish(event)
