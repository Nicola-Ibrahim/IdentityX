from datetime import datetime, timezone, timedelta

from .....building_blocks.domain.result import Result
from ....domain.account.account import Account
from ....domain.account.value_objects.email import Email
from ....domain.account.value_objects.external_identity import ExternalIdentity
from ....domain.session.session import Session
from ....domain.session.value_objects.refresh_token import RefreshToken
from ....domain.session.value_objects.session_id import SessionId
from ....domain.audit.audit_action import AuditAction
from ....domain.services.audit_service import AuditService
from ....domain.interfaces.account_repository import BaseAccountRepository
from ....domain.interfaces.session_repository import BaseSessionRepository
from ....domain.interfaces.audit_repository import BaseAuditRepository
from ...interfaces.social_provider import BaseSocialAuthenticationProvider
from ...interfaces.jwt import TokenPayload, TokenService
from .dtos import AuthDTO, TokenPair

class SocialAuthenticationService:
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        audit_repo: BaseAuditRepository,
        token_service: TokenService,
        audit_service: AuditService,
        providers: dict[str, BaseSocialAuthenticationProvider],
    ) -> None:
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._audit_repo = audit_repo
        self._token_service = token_service
        self._audit = audit_service
        self._providers = {p.lower(): v for p, v in providers.items()}

    async def _issue_session(
        self, account: Account, ip_address: str, user_agent: str, action: AuditAction = AuditAction.LOGIN_SUCCESS
    ) -> TokenPair:
        """Internal helper to issue a new session and JWT token pair."""
        session_id = SessionId.create()
        # Default TTL of 12 hours, same as SessionService
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
        account = await self._account_repo.get_by_external_identity(external_id.provider, external_id.provider_user_id)

        if not account:
            # 4. Check if email exists
            account = await self._account_repo.get_by_email(profile["email"])

            if account:
                # Link existing account
                account.link_external_identity(external_id)
                await self._account_repo.update(account)
                audit_entry = self._audit.create_entry(
                    AuditAction.SOCIAL_LINKED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"provider": external_id.provider},
                )
                await self._audit_repo.add(audit_entry)
            else:
                # 5. Register new account via SSO
                account = Account.register_from_social(
                    email=Email.create(profile["email"]), external_identity=external_id
                )
                account.verify()  # SSO emails are trusted
                await self._account_repo.add(account)
                audit_entry = self._audit.create_entry(
                    AuditAction.ACCOUNT_REGISTERED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"method": f"{external_id.provider}_sso"},
                )
                await self._audit_repo.add(audit_entry)

        # 6. Issue session
        tokens = await self._issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)
        return AuthDTO(tokens=tokens)
