from typing import Any
from src.shared.building_blocks.domain.rule import BaseBusinessRule


class EnabledMfaMustHaveSecretAndRecoveryCodesRule(BaseBusinessRule):
    enabled: bool
    secret: Any
    recovery_codes: list[Any]
    code: str = "EnabledMfaMustHaveSecretAndRecoveryCodes"
    message: str = "Enabled MFA must have a secret and recovery codes."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if self.enabled:
            if not self.secret or not self.recovery_codes:
                return True
        return False
