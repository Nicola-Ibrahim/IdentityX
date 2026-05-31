"""Domain event emitted when an account completes verification."""

from src.building_blocks.domain.events import DomainEvent


class AccountVerifiedEvent(DomainEvent):
    account_id: str
