"""Domain event emitted when an account is deactivated."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class AccountDeactivatedEvent(DomainEvent):
    account_id: str
