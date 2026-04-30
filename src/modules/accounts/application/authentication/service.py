import uuid
from datetime import datetime, timedelta, timezone

from .....database.decorators import transactional
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.interfaces.unit_of_work import BaseUnitOfWork
from ...domain.session.session import Session
from ...domain.session.value_objects.refresh_token import RefreshToken
from ...domain.session.value_objects.session_id import SessionId
from ..interfaces.jwt import TokenPayload, TokenService
from ..interfaces.password_hasher import BasePasswordHasher
from .issue_token_pair_dto import IssuedTokenPairDTO


class AuthenticationService:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        password_hasher: BasePasswordHasher,
        token_service: TokenService,
        session_ttl: timedelta | None = None,
    ) -> None:
        self.uow = uow
        self._hasher = password_hasher
        self._token_service = token_service
        self._session_ttl = session_ttl or timedelta(hours=12)

    @transactional
    async def authenticate(self, email: str, password: str) -> IssuedTokenPairDTO:
        """Authenticate user and issue a new token pair."""
        account = await self.uow.accounts.get_by_email(str(Email.create(email)))

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
        access, refresh = self._token_service.create_tokens(
            TokenPayload(sub=str(account.id.value), sid=str(session_id.value))
        )

        # 3. Create domain session
        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self.uow.sessions.add(session)

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    @transactional
    async def refresh_session(self, refresh_token_str: str) -> IssuedTokenPairDTO:
        """Rotate tokens using a valid refresh token."""
        # 1. Validate JWT structure and signature
        claims = self._token_service.validate_refresh_token(refresh_token_str)

        # 2. Load and validate domain session
        session = await self.uow.sessions.get_by_refresh_token(RefreshToken.create(refresh_token_str))

        if not session:
            raise ValueError("Session not found")

        if not session.is_active or session.is_revoked:
            raise ValueError("Session is no longer active or has been revoked")

        if session.is_expired():
            raise ValueError("Session has expired")

        # 3. Revoke old session (single-use rotation)
        session.revoke()
        await self.uow.sessions.update(session)

        # 4. Issue new session and tokens
        result = await self.authenticate_by_id(claims.sub)
        return result

    @transactional
    async def authenticate_by_id(self, account_id: str) -> IssuedTokenPairDTO:
        """Issue tokens for an already verified account (internal use)."""
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(account_id)))
        if not account:
            raise ValueError("Account not found")

        # 1. Prepare session metadata
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        # 2. Issue JWT tokens
        access, refresh = self._token_service.create_tokens(TokenPayload(sub=account_id, sid=str(session_id.value)))

        # 3. Create domain session
        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self.uow.sessions.add(session)

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    @transactional
    async def logout(self, refresh_token_str: str) -> None:
        """Revoke a session based on the refresh token."""
        try:
            self._token_service.validate_refresh_token(refresh_token_str)

            # Revoke domain session
            session = await self.uow.sessions.get_by_refresh_token(RefreshToken.create(refresh_token_str))
            if session:
                session.revoke()
                await self.uow.sessions.update(session)
        except Exception:
            # Logout should be silent if token is already invalid
            pass

    def get_current_account_id(self, access_token_str: str) -> str:
        """Validate an access token and return the account ID."""
        claims = self._token_service.validate_access_token(access_token_str)
        return claims.sub
