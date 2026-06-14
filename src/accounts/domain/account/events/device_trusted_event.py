"""Domain event emitted when a new device is trusted."""

from src.shared.building_blocks.domain.events import DomainEvent


class DeviceTrustedEvent(DomainEvent):
    account_id: str
    device_hash: str
