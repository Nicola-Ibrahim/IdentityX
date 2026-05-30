from typing import override
import uuid

from pydantic import BaseModel

from src.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.application.commands.helpers import issue_session
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.services.audit_service import AuditService
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.application.dtos.auth import TokenPair
from src.accounts.application.interfaces.jwt import TokenService


class RefreshSessionCommand(BaseModel, BaseCommand[TokenPair]):
    refresh_token: str


class RefreshSessionHandler(BaseCommandHandler[RefreshSessionCommand, TokenPair]):
    def __init__(
        self,
        token_service: TokenService,
        session_repo: BaseSessionRepository,
        account_repo: BaseAccountRepository,
        audit_repo: BaseAuditRepository,
        audit_service: AuditService,
    ):
        self._token_service = token_service
        self._session_repo = session_repo
        self._account_repo = account_repo
        self._audit_repo = audit_repo
        self._audit = audit_service

    @override
    async def handle(self, command: RefreshSessionCommand) -> TokenPair:
        claims = self._token_service.validate_refresh_token(command.refresh_token)
        session = await self._session_repo.get_by_refresh_token(RefreshToken.create(command.refresh_token))

        if not session:
            raise ValueError("Session not found")

        if not session.is_active or session.is_revoked:
            raise ValueError("Session is no longer active or has been revoked")

        if session.is_expired():
            raise ValueError("Session has expired")

        session.revoke()
        await self._session_repo.update(session)

        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        return await issue_session(
            account=account,
            ip_address="internal",
            user_agent="token_rotation",
            token_service=self._token_service,
            session_repo=self._session_repo,
            audit_repo=self._audit_repo,
            audit_service=self._audit,
            action=AuditAction.SESSION_REFRESHED,
        )
