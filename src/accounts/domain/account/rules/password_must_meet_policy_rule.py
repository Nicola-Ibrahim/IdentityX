"""Business rule enforcing the password strength policy."""

from dataclasses import dataclass, field

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule


@dataclass(slots=True)
class PasswordMustMeetPolicyRule(BaseBusinessRule):
    """Ensure a password satisfies basic strength requirements."""

    password: str
    min_length: int = 8
    code: ErrorCode = field(default=ErrorCode.INVALID_PASSWORD, init=False)
    message: str = field(default="Password does not meet minimum strength requirements.", init=False)
    error_type: ErrorType = field(default=ErrorType.VALIDATION_ERROR, init=False)

    def is_broken(self) -> bool:
        return not self.password or len(self.password) < self.min_length
