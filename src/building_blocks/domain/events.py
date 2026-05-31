import datetime
import uuid

from pydantic import BaseModel, Field
from src.building_blocks.application.mediator.messages.notifications import BaseNotification


class DomainEvent(BaseNotification, BaseModel):
    """Base class for the domain event"""

    # Auto-populate identifiers; keep them out of __init__ so subclasses can add required fields.
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, init=False)
    occurred_on: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), init=False
    )

    def to_dict(self) -> dict:
        """Serialize the event for logging or the outbox."""
        raw = self.model_dump()
        raw["event_id"] = str(self.event_id)
        raw["occurred_on"] = self.occurred_on.isoformat()
        return raw
