"""Domain event emitted when MFA is disabled for an account."""

from src.building_blocks.domain.events import DomainEvent


class MfaDisabledEvent(DomainEvent):
    account_id: str
