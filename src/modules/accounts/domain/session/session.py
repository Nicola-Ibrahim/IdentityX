from datetime import datetime, timezone

from pydantic import Field

from .....building_blocks.domain.aggregate_root import AggregateRoot
from ..account.value_objects.account_id import AccountId
from .rules.session_expiration_must_be_future_rule import SessionExpirationMustBeFutureRule
from .value_objects.refresh_token import RefreshToken
from .value_objects.session_id import SessionId
from .value_objects.session_status import SessionStatus


class Session(AggregateRoot[SessionId]):
    """Session aggregate representing an authenticated session for an account."""

    _id: SessionId
    _account_id: AccountId
    _refresh_token: RefreshToken
    _expires_at: datetime
    _status: SessionStatus = Field(default_factory=SessionStatus.active)
    _is_revoked: bool = Field(default=False, repr=False)

    @property
    def account_id(self) -> AccountId:
        return self._account_id

    @property
    def refresh_token(self) -> RefreshToken:
        return self._refresh_token

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def is_active(self) -> bool:
        return self._status.is_active

    @property
    def is_revoked(self) -> bool:
        return self._is_revoked

    def is_expired(self) -> bool:
        """Check if the session has naturally expired based on time."""
        return datetime.now(timezone.utc) >= self._expires_at

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
            _id=session_id or SessionId.create(),
            _account_id=account_id,
            _refresh_token=refresh_token,
            _expires_at=expires_at,
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
            _id=id,
            _account_id=account_id,
            _refresh_token=refresh_token,
            _expires_at=expires_at,
            _status=status,
            _is_revoked=is_revoked,
        )
        if created_at:
            session._created_at = created_at
        if updated_at:
            session._updated_at = updated_at
        return session

    def revoke(self) -> None:
        if self._status.is_active:
            self._status = self._status.revoke()
            self._is_revoked = True

    def expire(self) -> None:
        if self._status.is_active:
            self._status = self._status.revoke()
