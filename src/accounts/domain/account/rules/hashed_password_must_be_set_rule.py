from building_blocks.domain.rule import BaseBusinessRule


class HashedPasswordMustBeSetRule(BaseBusinessRule):
    """Ensure the hashed password string is present."""

    hashed_password: str
    code: str = "ValidationError"
    message: str = "Hashed password cannot be empty."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return not self.hashed_password.strip()
