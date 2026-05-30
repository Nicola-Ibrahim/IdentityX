from src.building_blocks.domain.rule import BaseBusinessRule


class PasswordMustMeetPolicyRule(BaseBusinessRule):
    """Ensure a password satisfies basic strength requirements."""

    password: str
    min_length: int = 8
    code: str = "InvalidPassword"
    message: str = "Password does not meet minimum strength requirements."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return not self.password or len(self.password) < self.min_length
