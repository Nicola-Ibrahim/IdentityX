import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from ....buckets.database.decorators import db
from ....building_blocks.domain.result import Result
from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ...domain.session.session import Session
from ...domain.session.value_objects.refresh_token import RefreshToken
from ...domain.session.value_objects.session_id import SessionId
from ..audit.audit_action import AuditAction
from ..audit.service import AuditService
from ..interfaces.jwt import TokenPayload, TokenService
from .dtos import TokenPair


class SessionService:
    """
    Handles session lifecycle management: issuing tokens, rotating them,
    and revoking active sessions.
    """

    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        token_service: TokenService,
        audit_service: AuditService,
        session_ttl: timedelta | None = None,
    ) -> None:
        self.uow = uow
        self._token_service = token_service
        self._audit = audit_service
        self._session_ttl = session_ttl or timedelta(hours=12)

    @db.transactional
    async def issue_session(
        self, account: Any, ip_address: str, user_agent: str, action: AuditAction = AuditAction.LOGIN_SUCCESS
    ) -> TokenPair:
        """Issue a new session and JWT token pair for an account."""
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        access, refresh = self._token_service.create_tokens(
            TokenPayload(sub=str(account.id.value), sid=str(session_id.value))
        )

        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self.uow.sessions.add(session)
        await self._audit.log(action, ip_address, user_agent, account_id=str(account.id.value))

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    @Result.capture
    @db.transactional
    async def refresh_session(self, refresh_token_str: str) -> TokenPair:
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
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        return await self.issue_session(account, "internal", "token_rotation", action=AuditAction.SESSION_REFRESHED)

    @Result.capture
    @db.transactional
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

    @Result.capture
    @db.transactional
    async def revoke_all_sessions(self, account_id: str) -> None:
        """Forcefully revoke all active sessions for an account."""
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        await self.uow.sessions.revoke_all_for_account(account_id_vo)

    def get_current_account_id(self, access_token_str: str) -> str:
        """Validate an access token and return the account ID."""
        claims = self._token_service.validate_access_token(access_token_str)
        return claims.sub

    def get_public_key(self) -> dict:
        """Return the public key in JWK format."""
        return self._token_service.get_public_key_jwk()
