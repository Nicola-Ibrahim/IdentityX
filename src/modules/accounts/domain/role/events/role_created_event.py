"""Event emitted when a role is created."""

from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass(slots=True)
class RoleCreatedEvent(DomainEvent):
    role_id: str
    name: str
