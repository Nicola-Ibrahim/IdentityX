"""Domain event emitted when an account completes verification."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class AccountVerifiedEvent(DomainEvent):
    account_id: str
