from src.shared.building_blocks.domain.rule import BaseBusinessRule


class AccountCannotBeDeactivatedIfAlreadyInactiveRule(BaseBusinessRule):
    is_active: bool
    code: str = "AccountAlreadyInactive"
    message: str = "Account is already inactive/suspended."
    error_type: str = "DomainValidationError"

    def is_broken(self) -> bool:
        return not self.is_active
