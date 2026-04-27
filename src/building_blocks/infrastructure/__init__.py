"""Infrastructure primitives shared by bounded contexts."""

from .event_bus import EventBus
from .outbox import Outbox, OutboxMessage
from .unit_of_work import UnitOfWork

__all__ = ["EventBus", "Outbox", "OutboxMessage", "UnitOfWork"]
