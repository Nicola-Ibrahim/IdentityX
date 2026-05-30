"""Event emitted when a new session is issued."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class SessionIssuedEvent(DomainEvent):
    session_id: str
    account_id: str
