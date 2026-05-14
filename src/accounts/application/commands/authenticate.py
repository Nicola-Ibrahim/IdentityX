from datetime import datetime, timedelta, timezone

from pydantic import BaseModel

from building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from accounts.domain.account.account import Account
from accounts.domain.account.value_objects.email import Email
from accounts.domain.audit.audit_action import AuditAction
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.domain.interfaces.audit_repository import BaseAuditRepository
from accounts.domain.interfaces.session_repository import BaseSessionRepository
from accounts.domain.services.audit_service import AuditService
from accounts.domain.session.session import Session
from accounts.domain.session.value_objects.refresh_token import RefreshToken
from accounts.domain.session.value_objects.session_id import SessionId
from accounts.application.dtos.auth import AuthDTO, MfaChallenge, TokenPair
from accounts.application.interfaces.jwt import TokenPayload, TokenService
from accounts.application.interfaces.password_hasher import BasePasswordHasher


class AuthenticateCommand(BaseModel, BaseCommand[AuthDTO]):
    email: str
    password: str
    ip_address: str
    user_agent: str
    device_hash: str | None = None


class AuthenticateHandler(BaseCommandHandler[AuthenticateCommand, AuthDTO]):
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        audit_repo: BaseAuditRepository,
        password_hasher: BasePasswordHasher,
        token_service: TokenService,
        audit_service: AuditService,
    ):
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._audit_repo = audit_repo
        self._hasher = password_hasher
        self._token_service = token_service
        self._audit = audit_service

    async def _issue_session(
        self, account: Account, ip_address: str, user_agent: str, action: AuditAction = AuditAction.LOGIN_SUCCESS
    ) -> TokenPair:
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)

        access, refresh = self._token_service.create_tokens(
            TokenPayload(sub=str(account.id.value), sid=str(session_id.value))
        )

        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self._session_repo.add(session)
        audit_entry = self._audit.create_entry(action, ip_address, user_agent, account_id=str(account.id.value))
        await self._audit_repo.add(audit_entry)

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=12 * 3600,
        )

    async def handle(self, command: AuthenticateCommand) -> AuthDTO:
        account = await self._account_repo.get_by_email(str(Email.create(command.email)))

        if not account:
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED,
                command.ip_address,
                command.user_agent,
                details={"email": command.email, "reason": "user_not_found"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid credentials")

        if not self._hasher.verify(command.password, account.password.value):
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED,
                command.ip_address,
                command.user_agent,
                account_id=str(account.id.value),
                details={"reason": "invalid_password"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid credentials")

        if not account.can_login():
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED,
                command.ip_address,
                command.user_agent,
                account_id=str(account.id.value),
                details={"reason": "account_inactive_or_unverified"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Account not active or verified")

        if command.device_hash and account.is_device_trusted(command.device_hash):
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_SUCCESS,
                command.ip_address,
                command.user_agent,
                account_id=str(account.id.value),
                details={"trusted_device": True},
            )
            await self._audit_repo.add(audit_entry)
            tokens = await self._issue_session(account, command.ip_address, command.user_agent)
            return AuthDTO(tokens=tokens)

        mfa_token = self._token_service.create_mfa_token(TokenPayload(sub=str(account.id.value)))

        log_action = AuditAction.MFA_REQUIRED if account.mfa.enabled else AuditAction.MFA_SETUP_INITIATED
        audit_entry = self._audit.create_entry(
            log_action, command.ip_address, command.user_agent, account_id=str(account.id.value)
        )
        await self._audit_repo.add(audit_entry)

        return AuthDTO(
            requires_mfa=True,
            mfa=MfaChallenge(mfa_token=mfa_token, mfa_setup_required=not account.mfa.enabled),
        )
