"""Event emitted when a session is revoked."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class SessionRevokedEvent(DomainEvent):
    session_id: str
    account_id: str
