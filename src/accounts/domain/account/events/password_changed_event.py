"""Domain event emitted when an account updates its password."""

from src.building_blocks.domain.events import DomainEvent


class PasswordChangedEvent(DomainEvent):
    account_id: str
