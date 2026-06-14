"""Domain event emitted when MFA is enabled for an account."""

from src.shared.building_blocks.domain.events import DomainEvent


class MfaEnabledEvent(DomainEvent):
    account_id: str
