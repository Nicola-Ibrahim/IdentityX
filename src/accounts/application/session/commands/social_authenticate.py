from typing import override
from pydantic import BaseModel

from src.shared.building_blocks.application.events.base_event_bus import BaseEventBus
from src.shared.building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from src.accounts.domain.account.account import Account
from src.accounts.domain.account.value_objects.email import Email
from src.accounts.domain.account.value_objects.external_identity import ExternalIdentity
from src.accounts.domain.audit.audit_action import AuditAction
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.domain.audit.repositories.audit_repository import BaseAuditRepository
from src.accounts.domain.session.repositories.session_repository import BaseSessionRepository
from src.accounts.domain.audit.services.audit_service import AuditService
from src.accounts.application.session.commands.helpers import issue_session
from src.accounts.application.session.dtos.session import AuthDTO
from src.accounts.domain.session.services.token_service import TokenService
from src.accounts.application.providers import SocialProviders


class SocialAuthenticateCommand(BaseModel, BaseCommand[AuthDTO]):
    provider_name: str
    code: str
    ip_address: str
    user_agent: str


class SocialAuthenticateHandler(BaseCommandHandler[SocialAuthenticateCommand, AuthDTO]):
    def __init__(
        self,
        providers: SocialProviders,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        audit_repo: BaseAuditRepository,
        audit_service: AuditService,
        token_service: TokenService,
        event_bus: BaseEventBus,
    ):
        self._providers = providers
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._audit_repo = audit_repo
        self._audit = audit_service
        self._token_service = token_service
        self._event_bus = event_bus

    @override
    async def handle(self, command: SocialAuthenticateCommand) -> AuthDTO:
        provider = self._providers.get(command.provider_name)
        if not provider:
            raise ValueError(f"Social provider '{command.provider_name}' is not supported.")

        profile = await provider.fetch_profile(command.code)
        external_id = ExternalIdentity.create(profile["provider"], profile["provider_user_id"])

        account = await self._account_repo.get_by_external_identity(external_id.provider, external_id.provider_user_id)

        if not account:
            account = await self._account_repo.get_by_email(profile["email"])

            if account:
                account.link_external_identity(external_id)
                await self._account_repo.update(account)
                await self._event_bus.publish_all(account.pull_events())
                audit_entry = self._audit.create_entry(
                    AuditAction.SOCIAL_LINKED,
                    command.ip_address,
                    command.user_agent,
                    account_id=str(account.id.value),
                    details={"provider": external_id.provider},
                )
                await self._audit_repo.add(audit_entry)
            else:
                account = Account.register_from_social(
                    email=Email.create(profile["email"]), external_identity=external_id
                )
                account.verify()
                await self._account_repo.add(account)
                await self._event_bus.publish_all(account.pull_events())
                audit_entry = self._audit.create_entry(
                    AuditAction.ACCOUNT_REGISTERED,
                    command.ip_address,
                    command.user_agent,
                    account_id=str(account.id.value),
                    details={"method": f"{external_id.provider}_sso"},
                )
                await self._audit_repo.add(audit_entry)

        tokens = await issue_session(
            account=account,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
            token_service=self._token_service,
            session_repo=self._session_repo,
            audit_repo=self._audit_repo,
            audit_service=self._audit,
            action=AuditAction.LOGIN_SUCCESS,
            event_bus=self._event_bus,
        )
        return AuthDTO(tokens=tokens)
