import datetime
import uuid

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for the domain event"""

    # Auto-populate identifiers; keep them out of __init__ so subclasses can add required fields.
    _event_id: uuid.UUID = Field(default_factory=uuid.uuid4, init=False)
    _occurred_on: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), init=False
    )

    @property
    def id(self) -> uuid.UUID:
        """Get the ID of the domain event."""
        return self._event_id

    @property
    def occurred_on(self) -> datetime.datetime:
        """Get the timestamp when the event occurred."""
        return self._occurred_on

    def to_dict(self) -> dict:
        """Serialize the event for logging or the outbox."""
        raw = self.model_dump()
        raw["event_id"] = str(self._event_id)
        raw["occurred_on"] = self._occurred_on.isoformat()
        return raw
