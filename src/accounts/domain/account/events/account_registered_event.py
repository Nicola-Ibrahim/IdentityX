"""Domain event emitted when a new account is registered."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class AccountRegisteredEvent(DomainEvent):
    account_id: str
    email: str
