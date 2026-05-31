from src.building_blocks.domain.rule import BaseBusinessRule


class AccountCannotBeVerifiedTwiceRule(BaseBusinessRule):
    is_verified: bool
    code: str = "AccountAlreadyVerified"
    message: str = "Account is already verified."
    error_type: str = "DomainValidationError"

    def is_broken(self) -> bool:
        return self.is_verified
