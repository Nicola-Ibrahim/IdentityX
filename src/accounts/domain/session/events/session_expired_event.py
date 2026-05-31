"""Event emitted when a session naturally expires."""

from src.building_blocks.domain.events import DomainEvent


class SessionExpiredEvent(DomainEvent):
    session_id: str
    account_id: str
