from ....buckets.database.decorators import db
from ....building_blocks.domain.result import Result
from ...domain.account.account import Account
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.external_identity import ExternalIdentity
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ..audit.audit_action import AuditAction
from ..audit.service import AuditService
from ..interfaces.social_provider import BaseSocialAuthenticationProvider
from .dtos import AuthDTO, TokenPair
from .sessions import SessionService


class SocialAuthenticationService:
    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        sessions: SessionService,
        audit_service: AuditService,
        providers: dict[str, BaseSocialAuthenticationProvider],
    ) -> None:
        self.uow = uow
        self._sessions = sessions
        self._audit = audit_service
        self._providers = {p.lower(): v for p, v in providers.items()}

    def _get_provider(self, provider_name: str) -> BaseSocialAuthenticationProvider:
        provider = self._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Social provider '{provider_name}' is not supported.")
        return provider

    @Result.capture
    async def get_authorization_url(self, provider_name: str, state: str) -> str:
        """Generate the authorization URL for the specified provider."""
        provider = self._get_provider(provider_name)
        return await provider.get_authorization_url(state)

    @Result.capture
    @db.transactional
    async def authenticate_callback(
        self,
        provider_name: str,
        code: str,
        ip_address: str,
        user_agent: str,
    ) -> AuthDTO:
        """Handle social auth callback and issue session tokens."""
        provider = self._get_provider(provider_name)

        # 1. Fetch normalized profile data from the infrastructure provider
        profile = await provider.fetch_profile(code)

        # 2. Create External Identity VO
        external_id = ExternalIdentity.create(profile["provider"], profile["provider_user_id"])

        # 3. Check if we already have this external identity
        account = await self.uow.accounts.get_by_external_identity(external_id.provider, external_id.provider_user_id)

        if not account:
            # 4. Check if email exists
            account = await self.uow.accounts.get_by_email(profile["email"])

            if account:
                # Link existing account
                account.link_external_identity(external_id)
                await self.uow.accounts.update(account)
                await self._audit.log(
                    AuditAction.SOCIAL_LINKED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"provider": external_id.provider},
                )
            else:
                # 5. Register new account via SSO
                account = Account.register_from_social(
                    email=Email.create(profile["email"]), external_identity=external_id
                )
                account.verify()  # SSO emails are trusted
                await self.uow.accounts.add(account)
                await self._audit.log(
                    AuditAction.ACCOUNT_REGISTERED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"method": f"{external_id.provider}_sso"},
                )

        # 6. Issue session
        tokens = await self._sessions.issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)
        return AuthDTO(tokens=tokens)
