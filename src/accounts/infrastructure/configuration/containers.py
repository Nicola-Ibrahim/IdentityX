from dependency_injector import containers, providers

from ...application.usecases.account.accounts import AccountService
from ...application.usecases.authentication.password_auth import PasswordAuthenticationService
from ...application.usecases.authentication.sessions import SessionService
from ...application.usecases.authentication.social_auth import SocialAuthenticationService
from ...domain.services.audit_service import AuditService
from ..authentication.social.google_provider import GoogleAuthenticationProvider
from ..crypto.jwt_token import JWTTokenService
from ..crypto.password_hasher import PBKDF2PasswordHasher
from ..messaging.email_notifier import ConsoleNotificationService
from ..persistence.repositories.account import SQLBaseAccountRepository
from ..persistence.repositories.audit import SQLAuditLogRepository
from ..persistence.repositories.session import SQLBaseSessionRepository
from .settings import AccountsSettings


class AccountsDIContainer(containers.DeclarativeContainer):
    """Top-level dependency injection container for the Accounts Bounded Context."""

    async def stop(self) -> None:
        """Asynchronous stop of all container resources."""
        self.shutdown_resources()
        self.unwire()

    # -- Core & Configuration --
    settings = providers.Singleton(AccountsSettings)

    # -- Infrastructure: Security & Crypto (Internal) --
    _password_hasher = providers.Singleton(PBKDF2PasswordHasher)

    _token_service = providers.Singleton(
        JWTTokenService,
        private_key=settings.provided.JWT_PRIVATE_KEY,
        public_key=settings.provided.JWT_PUBLIC_KEY,
        algorithm=settings.provided.JWT_ALGORITHM,
        issuer=settings.provided.JWT_ISSUER,
        access_token_ttl_minutes=settings.provided.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_ttl_days=settings.provided.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )

    # -- Infrastructure: Messaging (Internal) --
    _notification_service = providers.Singleton(ConsoleNotificationService)

    # -- Persistence: Repositories (Internal) --
    _account_repo = providers.Factory(SQLBaseAccountRepository)
    _session_repo = providers.Factory(SQLBaseSessionRepository)
    _audit_repo = providers.Factory(SQLAuditLogRepository)

    _audit_service = providers.Factory(
        AuditService,
        audit_repo=_audit_repo,
    )

    # -- Application Services (Exposed) --
    accounts = providers.Factory(
        AccountService,
        account_repo=_account_repo,
        session_repo=_session_repo,
        password_hasher=_password_hasher,
        notification_service=_notification_service,
    )

    sessions = providers.Factory(
        SessionService,
        session_repo=_session_repo,
        account_repo=_account_repo,
        audit_repo=_audit_repo,
        token_service=_token_service,
        audit_service=_audit_service,
    )

    password_auth = providers.Factory(
        PasswordAuthenticationService,
        account_repo=_account_repo,
        session_repo=_session_repo,
        audit_repo=_audit_repo,
        password_hasher=_password_hasher,
        token_service=_token_service,
        audit_service=_audit_service,
    )

    social_auth = providers.Factory(
        SocialAuthenticationService,
        account_repo=_account_repo,
        session_repo=_session_repo,
        audit_repo=_audit_repo,
        token_service=_token_service,
        audit_service=_audit_service,
        providers=providers.Dict(
            {
                "google": providers.Factory(
                    GoogleAuthenticationProvider,
                    client_id=settings.provided.GOOGLE_CLIENT_ID,
                    client_secret=settings.provided.GOOGLE_CLIENT_SECRET,
                    redirect_uri=settings.provided.GOOGLE_REDIRECT_URI,
                    auth_url=settings.provided.GOOGLE_AUTH_URL,
                    server_metadata_url=settings.provided.GOOGLE_METADATA_URL,
                ),
            }
        ),
    )
