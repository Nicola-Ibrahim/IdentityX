from datetime import datetime, timezone
from pydantic import Field

from src.shared.building_blocks.domain.aggregate_root import AggregateRoot
from src.accounts.domain.session.rules.session_expiration_must_be_future_rule import SessionExpirationMustBeFutureRule
from src.accounts.domain.session.rules.session_cannot_be_revoked_if_already_inactive_rule import SessionCannotBeRevokedIfAlreadyInactiveRule
from src.accounts.domain.session.value_objects.account_id import AccountId
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.domain.session.value_objects.session_status import SessionStatus

from src.accounts.domain.session.events.session_issued_event import SessionIssuedEvent
from src.accounts.domain.session.events.session_revoked_event import SessionRevokedEvent
from src.accounts.domain.session.events.session_expired_event import SessionExpiredEvent


class Session(AggregateRoot[SessionId]):
    """Session aggregate representing an authenticated session for an account."""

    id: SessionId
    account_id: AccountId
    refresh_token: RefreshToken
    expires_at: datetime
    status: SessionStatus = Field(default_factory=SessionStatus.active)

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
        session = cls(
            id=session_id or SessionId.create(),
            account_id=account_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        session.record_event(
            SessionIssuedEvent(
                session_id=str(session.id.value),
                account_id=str(session.account_id.value),
                refresh_token=str(session.refresh_token.value),
                expires_at=session.expires_at,
            )
        )
        return session

    @classmethod
    def from_data(
        cls,
        id: SessionId,
        account_id: AccountId,
        refresh_token: RefreshToken,
        expires_at: datetime,
        status: SessionStatus,
        is_revoked: bool,  # Keep parameter for backward compatibility in constructor but map to status
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> "Session":
        """Reconstitute a session from existing data."""
        # Ensure status reflects is_revoked if passed as true
        final_status = SessionStatus.revoked() if is_revoked else status
        session = cls(
            id=id,
            account_id=account_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            status=final_status,
        )
        if created_at:
            session.created_at = created_at
        if updated_at:
            session.updated_at = updated_at
        return session

    def revoke(self) -> None:
        self.check_rules(SessionCannotBeRevokedIfAlreadyInactiveRule(is_active=self.status.is_active))
        self.status = self.status.revoke()
        self.touch()
        self.record_event(SessionRevokedEvent(session_id=str(self.id.value), account_id=str(self.account_id.value)))

    def expire(self) -> None:
        self.check_rules(SessionCannotBeRevokedIfAlreadyInactiveRule(is_active=self.status.is_active))
        self.status = self.status.revoke()
        self.touch()
        self.record_event(SessionExpiredEvent(session_id=str(self.id.value), account_id=str(self.account_id.value)))

    @property
    def is_active(self) -> bool:
        return self.status.is_active

    @property
    def is_revoked(self) -> bool:
        return not self.status.is_active
