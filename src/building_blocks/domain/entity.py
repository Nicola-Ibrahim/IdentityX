from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from .events import DomainEvent
from .exceptions import BusinessRuleValidationException
from .rule import BaseBusinessRule

TEntityId = TypeVar("TEntityId")


class Entity(Generic[TEntityId], BaseModel):
    """Base class for all domain entities."""

    _id: TEntityId
    # Managed internally; exclude from generated __init__ so subclasses can add required fields.
    _created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    _updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    _version: int = Field(default=0, init=False)
    _events: list[DomainEvent] = Field(default_factory=list, init=False, repr=False)

    @property
    def id(self) -> TEntityId:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def version(self) -> int:
        return self._version

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Entity) and other._id == self._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"

    def touch(self) -> None:
        """Update the modification timestamp."""
        self._updated_at = datetime.now(timezone.utc)
        self._version += 1

    def copy(self, **changes: Any) -> "Entity[TEntityId]":
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
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    # Backwards compatible helpers ------------------------------------------------
    def add_event(self, event: DomainEvent) -> None:
        self.record_event(event)

    def get_events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()

    # ------------------------------------------------------------------ #
    # Business rules
    # ------------------------------------------------------------------ #
    def check_rules(self, *rules: BaseBusinessRule) -> None:
        for rule in rules:
            if rule.is_broken():
                raise BusinessRuleValidationException(rule)
