"""Domain event emitted when an account changes its email address."""

from src.shared.building_blocks.domain.events import DomainEvent


class EmailChangedEvent(DomainEvent):
    account_id: str
    new_email: str
