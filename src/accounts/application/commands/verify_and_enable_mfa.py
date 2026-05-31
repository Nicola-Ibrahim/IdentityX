from typing import override
import uuid
from datetime import datetime, timedelta, timezone

import pyotp
from pydantic import BaseModel

from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.account import Account
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.services.audit_service import AuditService
from src.accounts.domain.session.session import Session
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.domain.session.value_objects.mfa_token import MfaToken
from src.accounts.application.dtos.account import AccountDTO
from src.accounts.application.dtos.auth import TokenPair
from src.accounts.domain.services.token_service import TokenPayload, TokenService


class VerifyAndEnableMfaCommand(BaseModel, BaseCommand[AccountDTO]):
    mfa_token: str
    totp_code: str
    secret: str
    recovery_codes: list[str]
    ip_address: str
    user_agent: str


class VerifyAndEnableMfaHandler(BaseCommandHandler[VerifyAndEnableMfaCommand, AccountDTO]):
    def __init__(
        self,
        token_service: TokenService,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        audit_repo: BaseAuditRepository,
        audit_service: AuditService,
    ):
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
            refresh_token=refresh,
            expires_at=expires_at,
            session_id=session_id,
        )

        await self._session_repo.add(session)
        audit_entry = self._audit.create_entry(action, ip_address, user_agent, account_id=account.id)
        await self._audit_repo.add(audit_entry)

        return TokenPair(
            access_token=access.value,
            refresh_token=refresh.value,
            expires_in=12 * 3600,
        )

    @override
    async def handle(self, command: VerifyAndEnableMfaCommand) -> AccountDTO:
        claims = self._token_service.validate_mfa_token(MfaToken.create(command.mfa_token))
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        totp = pyotp.TOTP(command.secret)
        if not totp.verify(command.totp_code):
            audit_entry = self._audit.create_entry(
                AuditAction.MFA_FAILED,
                command.ip_address,
                command.user_agent,
                account_id=account.id,
                details={"reason": "invalid_totp_during_setup"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid TOTP code")

        account.enable_mfa(command.secret, command.recovery_codes)
        await self._account_repo.update(account)

        audit_entry = self._audit.create_entry(
            AuditAction.MFA_ENABLED, command.ip_address, command.user_agent, account_id=account.id
        )
        await self._audit_repo.add(audit_entry)

        tokens = await self._issue_session(
            account, command.ip_address, command.user_agent, action=AuditAction.LOGIN_SUCCESS
        )
        return AccountDTO(tokens=tokens)
