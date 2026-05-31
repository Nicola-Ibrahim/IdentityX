"""Domain event emitted when an account is anonymized for GDPR."""

from src.building_blocks.domain.events import DomainEvent


class AccountAnonymizedEvent(DomainEvent):
    account_id: str
