from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.building_blocks.domain.enums import ErrorCode, ErrorType
from src.building_blocks.domain.rule import BaseBusinessRule


@dataclass(slots=True)
class SessionExpirationMustBeFutureRule(BaseBusinessRule):
    expires_at: datetime
    code: ErrorCode = field(default=ErrorCode.SESSION_EXPIRATION_INVALID, init=False)
    message: str = field(default="Session expiration time must be set in the future", init=False)
    error_type: ErrorType = field(default=ErrorType.VALIDATION_ERROR, init=False)

    def is_broken(self) -> bool:
        return self.expires_at <= datetime.now(timezone.utc)
