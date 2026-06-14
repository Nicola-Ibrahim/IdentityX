"""Event emitted when a session is revoked."""

from src.shared.building_blocks.domain.events import DomainEvent


class SessionRevokedEvent(DomainEvent):
    session_id: str
    account_id: str
