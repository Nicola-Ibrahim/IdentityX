"""Domain event emitted when an account is activated."""

from src.building_blocks.domain.events import DomainEvent


class AccountActivatedEvent(DomainEvent):
    account_id: str
