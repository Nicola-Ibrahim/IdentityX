from dependency_injector import containers, providers
from .settings import AccountsSettings

from ...application.account.service import AccountService
from ...application.audit.service import AuditService
from ...application.authentication.service import AuthenticationService
from ...application.authentication.social_service import SocialAuthenticationService
from ..crypto.jwt_token import JWTTokenService
from ..crypto.password_hasher import PBKDF2PasswordHasher
from ..messaging.email_notifier import ConsoleNotificationService
from ..persistence.uow import SQLAlchemyUnitOfWork


class AccountsDIContainer(containers.DeclarativeContainer):
    """Top-level dependency injection container for the Accounts Bounded Context."""

    async def stop(self) -> None:
        """Asynchronous stop of all container resources."""
        self.shutdown_resources()
        self.unwire()

    # -- Core & Configuration --
    settings = providers.Singleton(AccountsSettings)
    session_factory = providers.Dependency()

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

    # -- Persistence: Unit of Work (Internal) --
    _unit_of_work = providers.Factory(
        SQLAlchemyUnitOfWork,
        session_factory=session_factory,
    )

    _audit_service = providers.Factory(
        AuditService,
        uow=_unit_of_work,
    )

    # -- Application Services (Exposed) --
    account_service = providers.Factory(
        AccountService,
        uow=_unit_of_work,
        password_hasher=_password_hasher,
        notification_service=_notification_service,
        audit_service=_audit_service,
    )

    authentication_service = providers.Factory(
        AuthenticationService,
        uow=_unit_of_work,
        password_hasher=_password_hasher,
        token_service=_token_service,
        audit_service=_audit_service,
    )

    social_authentication_service = providers.Factory(
        SocialAuthenticationService,
        uow=_unit_of_work,
        auth_service=authentication_service,
        audit_service=_audit_service,
        client_id=settings.provided.GOOGLE_CLIENT_ID,
        client_secret=settings.provided.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    )
