from dataclasses import dataclass, field

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule


@dataclass(slots=True)
class RefreshTokenMustBeSecureRule(BaseBusinessRule):
    """Rule ensuring refresh tokens are sufficiently random."""

    token: str
    min_length: int = 32
    code: ErrorCode = field(default=ErrorCode.INVALID_PASSWORD, init=False)
    message: str = field(default="Refresh token must be secure and meet minimum length requirements", init=False)
    error_type: ErrorType = field(default=ErrorType.VALIDATION_ERROR, init=False)

    def is_broken(self) -> bool:
        return not self.token or len(self.token) < self.min_length
