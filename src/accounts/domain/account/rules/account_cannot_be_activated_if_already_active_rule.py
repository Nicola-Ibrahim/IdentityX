from src.shared.building_blocks.domain.rule import BaseBusinessRule


class AccountCannotBeActivatedIfAlreadyActiveRule(BaseBusinessRule):
    is_active: bool
    code: str = "AccountAlreadyActive"
    message: str = "Account is already active."
    error_type: str = "DomainValidationError"

    def is_broken(self) -> bool:
        return self.is_active
