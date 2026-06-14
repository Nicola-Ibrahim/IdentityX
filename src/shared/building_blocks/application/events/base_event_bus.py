from abc import ABC, abstractmethod

from src.shared.building_blocks.domain.events import DomainEvent


class BaseEventBus(ABC):
    """
    Abstract contract for the domain event bus.

    Responsible for 1-to-many dispatching: a single domain event is broadcast
    to every handler that has subscribed to its type.

    Concrete implementations:
      - ``LocalEventBus``  — in-memory, suitable for a monolith / tests.
      - ``BrokerEventBus`` — wraps RabbitMQ / Redis / etc. for distributed systems.

    The key design invariant is that **switching implementations only requires
    changing the concrete class that is injected at startup** — no domain code,
    no repository code, and no handler code needs to change.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event to all registered handlers.

        Handlers are executed in subscription order.  If a handler raises, the
        remaining handlers are not called (fail-fast).  Override this behaviour
        in concrete implementations if you need fire-and-forget semantics.
        """
        ...

    @abstractmethod
    async def publish_all(self, events: list[DomainEvent]) -> None:
        """
        Convenience method: publish a list of events in the order they were
        recorded on the aggregate.  Delegates to ``publish()`` for each event.
        """
        ...
