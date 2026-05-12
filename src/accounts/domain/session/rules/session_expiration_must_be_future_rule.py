"""Rule ensuring session expiration time is set in the future."""

from datetime import datetime, timezone
from src.building_blocks.domain.rule import BaseBusinessRule

class SessionExpirationMustBeFutureRule(BaseBusinessRule):
    """Rule ensuring session expiration time is set in the future."""

    expires_at: datetime
    code: str = "SessionExpirationInvalid"
    message: str = "Session expiration time must be set in the future"
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        return self.expires_at <= datetime.now(timezone.utc)
