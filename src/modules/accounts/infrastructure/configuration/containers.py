from dependency_injector import containers, providers

from ...application.access_control.service import AccessControlService
from ...application.account.service import AccountService
from ...application.authentication.service import AuthenticationService
from ..crypto.jwt_token import JWTTokenFactory
from ..crypto.password_hasher import PBKDF2PasswordHasher
from ..messaging.email_notifier import ConsoleNotificationService
from ..persistence.repositories.sql_account_repo import SQLAccountRepository
from ..persistence.repositories.sql_role_repo import SQLRoleRepository
from ..persistence.repositories.sql_session_repo import SQLSessionRepository


class AccountsDIContainer(containers.DeclarativeContainer):
    """Top-level dependency injection container for the Accounts Bounded Context."""

    # -- Core & Configuration --
    config = providers.Configuration()
    _session_factory = providers.Dependency()

    # -- Infrastructure: Security & Crypto (Internal) --
    _password_hasher = providers.Singleton(PBKDF2PasswordHasher)

    _token_factory = providers.Singleton(
        JWTTokenFactory,
        private_key=config.jwt_private_key,
        public_key=config.jwt_public_key,
        algorithm=config.jwt_algorithm,
        issuer=config.jwt_issuer,
        access_token_ttl_minutes=config.jwt_access_token_expire_minutes,
        refresh_token_ttl_days=config.jwt_refresh_token_expire_days,
    )

    # -- Infrastructure: Messaging (Internal) --
    _notification_service = providers.Singleton(ConsoleNotificationService)

    # -- Persistence: Repositories (Internal) --
    _account_repository = providers.Singleton(
        SQLAccountRepository,
        session_factory=_session_factory,
    )
    _session_repository = providers.Singleton(
        SQLSessionRepository,
        session_factory=_session_factory,
    )
    _role_repository = providers.Singleton(
        SQLRoleRepository,
        session_factory=_session_factory,
    )

    # -- Application Services (Exposed) --
    account_service = providers.Factory(
        AccountService,
        account_repository=_account_repository,
        password_hasher=_password_hasher,
    )

    authentication_service = providers.Factory(
        AuthenticationService,
        account_repository=_account_repository,
        session_repository=_session_repository,
        password_hasher=_password_hasher,
        token_factory=_token_factory,
    )

    access_control_service = providers.Factory(
        AccessControlService,
        account_repo=_account_repository,
        role_repo=_role_repository,
    )
