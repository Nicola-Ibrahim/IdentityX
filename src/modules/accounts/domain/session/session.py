from datetime import datetime, timezone

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from .rules.session_expiration_must_be_future_rule import SessionExpirationMustBeFutureRule
from .value_objects.account_id import AccountId
from .value_objects.refresh_token import RefreshToken
from .value_objects.session_id import SessionId
from .value_objects.session_status import SessionStatus


class Session(AggregateRoot[SessionId]):
    """Session aggregate representing an authenticated session for an account."""

    id: SessionId
    account_id: AccountId
    refresh_token: RefreshToken
    expires_at: datetime
    status: SessionStatus = Field(default_factory=SessionStatus.active)
    is_revoked: bool = Field(default=False, repr=False)

    def is_expired(self) -> bool:
        """Check if the session has naturally expired based on time."""
        return datetime.now(timezone.utc) >= self.expires_at

    @classmethod
    def issue(
        cls,
        account_id: AccountId,
        refresh_token: RefreshToken,
        expires_at: datetime,
        session_id: SessionId | None = None,
    ) -> "Session":
        cls.check_rules(SessionExpirationMustBeFutureRule(expires_at=expires_at))
        return cls(
            id=session_id or SessionId.create(),
            account_id=account_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

    @classmethod
    def from_data(
        cls,
        id: SessionId,
        account_id: AccountId,
        refresh_token: RefreshToken,
        expires_at: datetime,
        status: SessionStatus,
        is_revoked: bool,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Session":
        """Reconstitute a session from existing data."""
        session = cls(
            id=id,
            account_id=account_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            status=status,
            is_revoked=is_revoked,
        )
        if created_at:
            session.created_at = created_at
        if updated_at:
            session.updated_at = updated_at
        return session

    def revoke(self) -> None:
        if self.status.is_active:
            self.status = self.status.revoke()
            self.is_revoked = True

    def expire(self) -> None:
        if self.status.is_active:
            self.status = self.status.revoke()
