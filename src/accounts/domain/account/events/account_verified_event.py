"""Domain event emitted when an account completes verification."""

from src.shared.building_blocks.domain.events import DomainEvent


class AccountVerifiedEvent(DomainEvent):
    account_id: str
