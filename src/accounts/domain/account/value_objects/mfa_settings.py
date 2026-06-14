from typing import Self
from pydantic import Field

from src.shared.building_blocks.domain.value_object import ValueObject
from src.accounts.domain.account.rules.enabled_mfa_must_have_secret_and_recovery_codes_rule import EnabledMfaMustHaveSecretAndRecoveryCodesRule
from src.accounts.domain.account.rules.mfa_secret_must_be_valid_rule import MfaSecretMustBeValidRule
from src.accounts.domain.account.rules.recovery_code_must_be_valid_rule import RecoveryCodeMustBeValidRule


class MfaSettings(ValueObject):
    """
    Value object representing the MFA configuration for an account.
    """

    enabled: bool = False
    secret: str | None = None
    recovery_codes: list[str] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        enabled: bool = False,
        secret: str | None = None,
        recovery_codes: list[str] = None,
    ) -> Self:
        """Factory method to enforce business rules during creation."""
        codes = recovery_codes or []
        
        # Enforce enabled MFA rules
        cls.check_rules(
            EnabledMfaMustHaveSecretAndRecoveryCodesRule(
                enabled=enabled,
                secret=secret,
                recovery_codes=codes,
            )
        )

        # Enforce content format rules if secret/codes are supplied
        if secret is not None:
            cls.check_rules(MfaSecretMustBeValidRule(secret=secret))
        for code in codes:
            cls.check_rules(RecoveryCodeMustBeValidRule(recovery_code=code))

        return cls(enabled=enabled, secret=secret, recovery_codes=codes)

    @classmethod
    def create_disabled(cls) -> Self:
        """Create a default disabled MFA state."""
        return cls.create(enabled=False, secret=None, recovery_codes=[])

    def enable(self, secret: str, recovery_codes: list[str]) -> "MfaSettings":
        """Return a new instance with MFA enabled."""
        return MfaSettings.create(enabled=True, secret=secret, recovery_codes=list(recovery_codes))

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
            return True, MfaSettings.create(enabled=self.enabled, secret=self.secret, recovery_codes=new_codes)
        return False, self
