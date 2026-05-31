"""Domain event emitted when an account is suspended."""

from src.building_blocks.domain.events import DomainEvent


class AccountSuspendedEvent(DomainEvent):
    account_id: str
