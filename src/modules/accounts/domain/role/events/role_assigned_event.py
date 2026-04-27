from dataclasses import dataclass

from src.building_blocks.domain.events import DomainEvent


@dataclass
class RoleAssignedEvent(DomainEvent):
    role_id: str
    account_id: str
