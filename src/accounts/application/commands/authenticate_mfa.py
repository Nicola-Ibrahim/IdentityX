import hashlib
import uuid
from datetime import datetime, timedelta, timezone
import pyotp
from pydantic import BaseModel
from src.building_blocks.application.commands import BaseCommand
from src.building_blocks.application.mediator import BaseCommand,  Handler
from src.accounts.application.dtos.account import AuthDTO
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.domain.services.audit_service import AuditService
from src.accounts.application.interfaces.jwt import TokenService, TokenPayload
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.application.dtos.auth import TokenPair
from src.accounts.domain.session.session import Session
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.account.account import Account

class AuthenticateMfaCommand(BaseCommand[AuthDTO], BaseModel):
    mfa_token: str
    ip_address: str
    user_agent: str
    totp_code: str | None = None
    recovery_code: str | None = None
    trust_device: bool = False

class AuthenticateMfaHandler(BaseCommandHandler[AuthenticateMfaCommand, AuthDTO]):
    def __init__(self,
                 token_service: TokenService,
                 account_repo: BaseAccountRepository,
                 session_repo: BaseSessionRepository,
                 audit_repo: BaseAuditRepository,
                 audit_service: AuditService):
        self._token_service = token_service
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._audit_repo = audit_repo
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

    async def handle(self, command: AuthenticateMfaCommand) -> AuthDTO:
        claims = self._token_service.validate_mfa_token(command.mfa_token)
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        if not account.mfa.enabled or not account.mfa.secret:
            raise ValueError("MFA not enabled for this account")

        mfa_verified = False
        if command.recovery_code:
            mfa_verified = account.consume_recovery_code(command.recovery_code)
            if not mfa_verified:
                audit_entry = self._audit.create_entry(
                    AuditAction.MFA_FAILED,
                    command.ip_address,
                    command.user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_recovery_code"},
                )
                await self._audit_repo.add(audit_entry)
                raise ValueError("invalid_recovery_code")

        elif command.totp_code:
            totp = pyotp.TOTP(account.mfa.secret)
            if totp.verify(command.totp_code):
                mfa_verified = True
            else:
                audit_entry = self._audit.create_entry(
                    AuditAction.MFA_FAILED,
                    command.ip_address,
                    command.user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_totp"},
                )
                await self._audit_repo.add(audit_entry)
                raise ValueError("invalid_totp")
        else:
            raise ValueError("Either TOTP code or recovery code must be provided")

        audit_entry = self._audit.create_entry(
            AuditAction.MFA_VERIFIED, command.ip_address, command.user_agent, account_id=str(account.id.value)
        )
        await self._audit_repo.add(audit_entry)

        new_device_token = None
        if command.trust_device:
            new_device_token = str(uuid.uuid4())
            device_hash = hashlib.sha256(new_device_token.encode()).hexdigest()
            account.trust_device(device_hash, command.user_agent, command.ip_address)
            await self._account_repo.update(account)
            audit_entry = self._audit.create_entry(
                AuditAction.TRUSTED_DEVICE_ADDED, command.ip_address, command.user_agent, account_id=str(account.id.value)
            )
            await self._audit_repo.add(audit_entry)

        dto = await self._issue_session(account, command.ip_address, command.user_agent, action=AuditAction.LOGIN_SUCCESS)

        if new_device_token:
            dto.trusted_device_token = new_device_token

        return AuthDTO(tokens=dto)
