import uuid
from datetime import datetime, timedelta, timezone

from ...domain.account.value_objects.email import Email
from ...domain.interfaces.account_repository import AccountRepository
from ...domain.interfaces.session_repository import SessionRepository
from ...domain.interfaces.token_denylist_repository import TokenDenylistRepository
from ...domain.session.session import Session
from ...domain.session.value_objects.refresh_token import RefreshToken
from ...domain.session.value_objects.session_id import SessionId
from ..interfaces.jwt import TokenFactory
from ..interfaces.password_hasher import IPasswordHasher
from ..interfaces.token_errors import TokenRevokedError
from .issue_token_pair_dto import IssuedTokenPairDTO


class AuthenticationService:
    def __init__(
        self,
        account_repository: AccountRepository,
        session_repository: SessionRepository,
        password_hasher: IPasswordHasher,
        token_factory: TokenFactory,
        token_denylist: TokenDenylistRepository,
        session_ttl: timedelta | None = None,
    ) -> None:
        self._accounts = account_repository
        self._sessions = session_repository
        self._hasher = password_hasher
        self._token_factory = token_factory
        self._denylist = token_denylist
        self._session_ttl = session_ttl or timedelta(hours=12)

    def authenticate(self, email: str, password: str) -> IssuedTokenPairDTO:
        """Authenticate user and issue a new token pair."""
        account = self._accounts.get_by_email(str(Email.create(email)))

        if not account:
            raise ValueError("Invalid credentials")
        if not self._hasher.verify(password, account.hashed_password.value):
            raise ValueError("Invalid credentials")
        if not account.can_login():
            raise ValueError("Account not active or verified")

        # 1. Prepare session metadata
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        # 2. Issue JWT tokens (including sid for session tracking)
        access, refresh = self._token_factory.create_tokens(
            {"sub": str(account.id.value), "sid": str(session_id.value)}
        )

        # 3. Create domain session
        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        self._sessions.add(session)

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    def refresh_session(self, refresh_token_str: str) -> IssuedTokenPairDTO:
        """Rotate tokens using a valid refresh token."""
        # 1. Validate JWT structure and signature
        claims = self._token_factory.validate_refresh_token(refresh_token_str)

        # 2. Check if this specific token was revoked
        if self._denylist.is_revoked(claims.jti):
            raise TokenRevokedError("Token has been revoked")

        # 3. Load and validate domain session
        if not claims.sid:
            raise ValueError("Invalid session in token")

        session_id = SessionId.create(uuid.UUID(claims.sid))
        session = self._sessions.get_by_id(session_id)
        if not session or not session.is_active or session.is_expired():
            # If session is dead, denylist the token just in case
            self._denylist.add(claims.jti, expires_at=claims.exp_datetime)
            raise ValueError("Session is no longer active")

        # 4. Revoke old session (single-use rotation)
        session.revoke()
        self._sessions.update(session)

        # 5. Denylist the used refresh token JTI
        self._denylist.add(claims.jti, expires_at=claims.exp_datetime)

        # 6. Issue new session and tokens
        return self.authenticate_by_id(claims.sub)

    def authenticate_by_id(self, account_id: str) -> IssuedTokenPairDTO:
        """Issue tokens for an already verified account (internal use)."""
        account = self._accounts.get_by_id(AccountId.create(uuid.UUID(account_id)))
        if not account:
            raise ValueError("Account not found")

        # 1. Prepare session metadata
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        # 2. Issue JWT tokens
        access, refresh = self._token_factory.create_tokens({"sub": account_id, "sid": str(session_id.value)})

        # 3. Create domain session
        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        self._sessions.add(session)

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    def logout(self, refresh_token_str: str) -> None:
        """Revoke a session and denylist the token."""
        try:
            claims = self._token_factory.validate_refresh_token(refresh_token_str)

            # Revoke domain session
            session_id = SessionId.create(uuid.UUID(claims.sid))
            session = self._sessions.get_by_id(session_id)
            if session:
                session.revoke()
                self._sessions.update(session)

            # Denylist the token
            self._denylist.add(claims.jti, expires_at=claims.exp_datetime)
        except Exception:
            # Logout should be silent if token is already invalid
            pass

    def get_current_account_id(self, access_token_str: str) -> str:
        """Validate an access token and return the account ID."""
        claims = self._token_factory.validate_access_token(access_token_str)

        if self._denylist.is_revoked(claims.jti):
            raise TokenRevokedError("Token has been revoked")

        return claims.sub
