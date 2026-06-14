from lagom import Container

from src.shared.building_blocks.application.events.base_event_bus import BaseEventBus
from src.shared.building_blocks.domain.events import DomainEvent
from src.shared.infrastructure.events.scanner import discover_event_handlers


class LocalEventBus(BaseEventBus):
    """
    In-memory, synchronous 1-to-many event bus.

    This class is a **pure publisher** — it has no knowledge of how handlers
    are discovered. All of that is handled internally by scanning and registering
    event handlers dynamically, resolving them with a native lagom ``Container``.

    Handlers are executed **sequentially** so that a shared ``AsyncSession``
    (from SQLAlchemy) is safe to use inside handlers without concurrency issues.
    """

    def __init__(self, container: Container) -> None:
        """
        Parameters
        ----------
        container:
            A native ``Container`` instance used to resolve handlers.
        """
        self._container = container
        self._event_registry = discover_event_handlers()

    async def publish(self, event: DomainEvent) -> None:
        """
        Dispatch *event* to every registered handler for its type.

        Handlers are called sequentially. If a handler raises, publishing
        stops immediately (fail-fast).
        """
        handler_classes = self._event_registry.get(type(event), [])
        for handler_class in handler_classes:
            handler = self._container[handler_class]
            await handler.handle(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        """Publish multiple events in order, delegating each to ``publish()``."""
        for event in events:
            await self.publish(event)
