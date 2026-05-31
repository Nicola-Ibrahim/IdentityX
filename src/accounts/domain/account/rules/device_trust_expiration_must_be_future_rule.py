from datetime import datetime, timezone
from src.building_blocks.domain.rule import BaseBusinessRule


class DeviceTrustExpirationMustBeFutureRule(BaseBusinessRule):
    expires_at: datetime
    code: str = "DeviceTrustExpirationMustBeFuture"
    message: str = "Device trust expiration date must be in the future."
    error_type: str = "ValidationError"

    def is_broken(self) -> bool:
        # Avoid naive/aware comparison by ensuring expires_at is timezone-aware
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp <= datetime.now(timezone.utc)
