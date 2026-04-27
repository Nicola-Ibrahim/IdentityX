"""Rule ensuring hashed passwords are non-empty."""

from dataclasses import dataclass, field

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule


@dataclass(slots=True)
class HashedPasswordMustBeSetRule(BaseBusinessRule):
    """Ensure the hashed password string is present."""

    hashed_password: str
    code: ErrorCode = field(default=ErrorCode.VALIDATION_ERROR, init=False)
    message: str = field(default="Hashed password cannot be empty.", init=False)
    error_type: ErrorType = field(default=ErrorType.VALIDATION_ERROR, init=False)

    def is_broken(self) -> bool:
        return not self.hashed_password.strip()
