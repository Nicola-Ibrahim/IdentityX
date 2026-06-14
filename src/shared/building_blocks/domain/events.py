import datetime
import uuid

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """
    Base class for all domain events.

    Domain events are plain value objects that record *something that happened*
    inside a domain aggregate.  They are produced by the domain layer and
    consumed by the application/infrastructure layers — the domain itself never
    depends on how they are dispatched.

    Intentionally does NOT extend any application-layer type (e.g. BaseNotification)
    so that the domain layer remains free of application-layer dependencies.
    """

    # Auto-populated; kept out of __init__ so subclasses only declare payload fields.
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, init=False)
    occurred_on: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), init=False
    )

    model_config = {"frozen": False}

    def to_dict(self) -> dict:
        """Serialize the event for logging, tracing, or the outbox pattern."""
        raw = self.model_dump()
        raw["event_id"] = str(self.event_id)
        raw["occurred_on"] = self.occurred_on.isoformat()
        return raw
