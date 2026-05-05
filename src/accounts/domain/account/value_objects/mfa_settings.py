from typing import Self

from pydantic import Field

from .....building_blocks.domain.value_object import ValueObject


class MfaSettings(ValueObject):
    """
    Value object representing the MFA configuration for an account.
    """

    enabled: bool = False
    secret: str | None = None
    recovery_codes: list[str] = Field(default_factory=list)

    @classmethod
    def create_disabled(cls) -> Self:
        """Create a default disabled MFA state."""
        return cls(enabled=False, secret=None, recovery_codes=[])

    def enable(self, secret: str, recovery_codes: list[str]) -> "MfaSettings":
        """Return a new instance with MFA enabled."""
        return MfaSettings(enabled=True, secret=secret, recovery_codes=list(recovery_codes))

    def disable(self) -> Self:
        """Return a new instance with MFA disabled."""
        return self.create_disabled()

    def verify_recovery_code(self, code: str) -> tuple[bool, "MfaSettings"]:
        """
        Verify and consume a recovery code.
        Returns (is_valid, new_mfa_settings).
        """
        if code in self.recovery_codes:
            new_codes = [c for c in self.recovery_codes if c != code]
            return True, MfaSettings(enabled=self.enabled, secret=self.secret, recovery_codes=new_codes)
        return False, self
