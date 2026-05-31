from datetime import datetime, timezone
from typing import Self
from pydantic import Field

from src.building_blocks.domain.value_object import ValueObject
from src.accounts.domain.account.rules.device_hash_must_be_valid_sha256_rule import DeviceHashMustBeValidSha256Rule
from src.accounts.domain.account.rules.device_trust_expiration_must_be_future_rule import DeviceTrustExpirationMustBeFutureRule
from src.accounts.domain.account.rules.ip_address_must_be_valid_rule import IpAddressMustBeValidRule
from src.accounts.domain.account.rules.user_agent_must_be_valid_rule import UserAgentMustBeValidRule


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

    @classmethod
    def create(
        cls,
        device_hash: str,
        user_agent: str,
        ip_address: str,
        expires_at: datetime,
    ) -> Self:
        cls.check_rules(
            DeviceHashMustBeValidSha256Rule(device_hash=device_hash),
            IpAddressMustBeValidRule(ip_address=ip_address),
            UserAgentMustBeValidRule(user_agent=user_agent),
            DeviceTrustExpirationMustBeFutureRule(expires_at=expires_at),
        )
        return cls(
            device_hash=device_hash,
            user_agent=user_agent.strip(),
            ip_address=ip_address.strip(),
            expires_at=expires_at,
        )

    def is_valid(self, device_hash: str, now: datetime | None = None) -> bool:
        """Check if this specific device matches the hash and is not expired."""
        check_time = now or datetime.now(timezone.utc)
        return self.device_hash == device_hash and self.expires_at > check_time
