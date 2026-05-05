"""Event emitted when a session naturally expires."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class SessionExpiredEvent(DomainEvent):
    session_id: str
    account_id: str
