"""Domain event emitted when an account is deactivated."""

from src.building_blocks.domain.events import DomainEvent


class AccountDeactivatedEvent(DomainEvent):
    account_id: str
