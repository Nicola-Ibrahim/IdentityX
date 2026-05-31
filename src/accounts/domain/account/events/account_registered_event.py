"""Domain event emitted when a new account is registered."""

from src.building_blocks.domain.events import DomainEvent


class AccountRegisteredEvent(DomainEvent):
    account_id: str
    email: str
    roles: list[str]
