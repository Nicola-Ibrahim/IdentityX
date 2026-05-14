from datetime import datetime, timezone

from pydantic import Field

from building_blocks.domain.value_object import ValueObject


class TrustedDevice(ValueObject):
    """
    Value object representing a device trusted for MFA bypass.
    Identified by its hash rather than a unique ID.
    """

    device_hash: str
    user_agent: str
    ip_address: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self, device_hash: str, now: datetime | None = None) -> bool:
        """Check if this specific device matches the hash and is not expired."""
        check_time = now or datetime.now(timezone.utc)
        return self.device_hash == device_hash and self.expires_at > check_time
