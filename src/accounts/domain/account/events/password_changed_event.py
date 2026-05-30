"""Domain event emitted when an account updates its password."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class PasswordChangedEvent(DomainEvent):
    account_id: str
