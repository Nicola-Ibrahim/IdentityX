from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .events import DomainEvent
from .exceptions import BusinessRuleValidationException
from .rule import BaseBusinessRule


class Entity[TEntityId](BaseModel):
    """Base class for all domain entities."""

    id: TEntityId
    # Managed internally; exclude from generated __init__ so subclasses can add required fields.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    version: int = Field(default=0, init=False)
    events: list[DomainEvent] = Field(default_factory=list, init=False, repr=False)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entity) and other.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r})"

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1

    def copy(self, **changes: Any) -> Entity[TEntityId]:
        """Create a modified copy of the entity."""
        return self.model_copy(**changes)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entity (recursively) into a dict."""
        raw = self.model_dump()
        raw.pop("_events", None)
        return {key: value.to_dict() if isinstance(value, Entity) else value for key, value in raw.items()}

    # ------------------------------------------------------------------ #
    # Domain events
    # ------------------------------------------------------------------ #
    def record_event(self, event: DomainEvent) -> None:
        self.events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self.events)
        self.events.clear()
        return events

    # Backwards compatible helpers ------------------------------------------------
    def add_event(self, event: DomainEvent) -> None:
        self.record_event(event)

    def get_events(self) -> list[DomainEvent]:
        return list(self.events)

    def clear_events(self) -> None:
        self.events.clear()

    # ------------------------------------------------------------------ #
    # Business rules
    # ------------------------------------------------------------------ #
    def check_rules(self, *rules: BaseBusinessRule) -> None:
        for rule in rules:
            if rule.is_broken():
                raise BusinessRuleValidationException(rule)
