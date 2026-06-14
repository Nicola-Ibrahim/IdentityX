from src.shared.building_blocks.domain.rule import BaseBusinessRule


class PasswordMustMeetPolicyRule(BaseBusinessRule):
    """Ensure a password satisfies basic strength requirements."""

    password: str
    min_length: int = 8
    max_length: int = 128
    code: str = "InvalidPassword"
    message: str = "Password must be between 8 and 128 characters long."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        if not self.password:
            return True
        return len(self.password) < self.min_length or len(self.password) > self.max_length
