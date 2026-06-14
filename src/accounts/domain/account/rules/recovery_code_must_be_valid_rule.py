from src.shared.building_blocks.domain.rule import BaseBusinessRule


class RecoveryCodeMustBeValidRule(BaseBusinessRule):
    recovery_code: str
    code: str = "InvalidRecoveryCode"
    message: str = "Recovery code must be valid and non-empty."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.recovery_code:
            return True
        if len(self.recovery_code) > 64:
            return True
        return False
