from authlib.integrations.httpx_client import AsyncOAuth2Client

from ....building_blocks.domain.result import Result
from ...domain.account.account import Account
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.external_identity import ExternalIdentity
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ..audit.audit_action import AuditAction
from ..audit.service import AuditService
from .issue_token_pair_dto import IssuedTokenPairDTO
from .service import AuthenticationService


class SocialAuthenticationService:
    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        auth_service: AuthenticationService,
        audit_service: AuditService,
        client_id: str,
        client_secret: str,
        server_metadata_url: str,
    ) -> None:
        self.uow = uow
        self._auth = auth_service
        self._audit = audit_service
        self._client_id = client_id
        self._client_secret = client_secret
        self._metadata_url = server_metadata_url

    @Result.capture
    async def authenticate_with_google(
        self, code: str, redirect_uri: str, ip_address: str, user_agent: str
    ) -> IssuedTokenPairDTO:
        """Handle Google OAuth2 callback and issue session tokens."""

        async with AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
        ) as client:
            await client.load_server_metadata(self._metadata_url)
            token = await client.fetch_token(
                url=client.metadata.get("token_endpoint"),
                code=code,
                redirect_uri=redirect_uri,
                grant_type="authorization_code",
            )

            # Use OpenID Connect to get user info
            user_info = await client.get(client.metadata.get("userinfo_endpoint"))
            user_data = user_info.json()

            email_str = user_data.get("email")
            google_id = user_data.get("sub")

            if not email_str or not google_id:
                raise ValueError("Invalid response from Google")

            async with self.uow:
                # 1. Check if we already have this external identity
                account = await self.uow.accounts.get_by_external_identity("google", google_id)

                if not account:
                    # 2. Check if email exists
                    account = await self.uow.accounts.get_by_email(email_str)

                    if account:
                        # Link existing account
                        account.link_external_identity("google", google_id)
                        await self.uow.accounts.update(account)
                        await self._audit.log(
                            AuditAction.SOCIAL_LINKED,
                            ip_address,
                            user_agent,
                            account_id=str(account.id.value),
                            details={"provider": "google"},
                        )
                    else:
                        # 3. Register new account via SSO
                        account = Account.register_from_social(
                            email=Email.create(email_str),
                            provider="google",
                            provider_user_id=google_id
                        )
                        account.verify()  # SSO emails are trusted
                        await self.uow.accounts.add(account)
                        await self._audit.log(
                            AuditAction.ACCOUNT_REGISTERED,
                            ip_address,
                            user_agent,
                            account_id=str(account.id.value),
                            details={"method": "google_sso"},
                        )

                await self.uow.commit()

                # 4. Issue session (MFA is usually bypassed for SSO if trusted, but we follow standard flow)
                # For this demo, we bypass MFA for SSO
                return await self._auth._issue_session(
                    account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS
                )
