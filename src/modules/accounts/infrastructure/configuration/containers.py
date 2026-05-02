from dependency_injector import containers, providers

from .....database import SQLAlchemySessionFactory, SQLAlchemySettings
from ...application.account.service import AccountService
from ...application.authentication.service import AuthenticationService
from ..crypto.jwt_token import JWTTokenService
from ..crypto.password_hasher import PBKDF2PasswordHasher
from ..messaging.email_notifier import ConsoleNotificationService
from ..persistence.uow import SQLAlchemyUnitOfWork


class AccountsDIContainer(containers.DeclarativeContainer):
    """Top-level dependency injection container for the Accounts Bounded Context."""

    async def stop(self) -> None:
        """Asynchronous stop of all container resources."""
        if self._session_factory.initialized:
            factory = self._session_factory()
            await factory.dispose()
        self.shutdown_resources()
        self.unwire()

    # -- Core & Configuration --
    config = providers.Configuration()

    @staticmethod
    def _create_session_factory(config: dict):
        settings = SQLAlchemySettings(**config)
        factory = SQLAlchemySessionFactory(settings)
        yield factory

    _session_factory = providers.Resource(
        _create_session_factory,
        config=config.database,
    )

    # -- Infrastructure: Security & Crypto (Internal) --
    _password_hasher = providers.Singleton(PBKDF2PasswordHasher)

    _token_service = providers.Singleton(
        JWTTokenService,
        private_key=config.backend.jwt_private_key,
        public_key=config.backend.jwt_public_key,
        algorithm=config.backend.jwt_algorithm,
        issuer=config.backend.jwt_issuer,
        access_token_ttl_minutes=config.backend.jwt_access_token_expire_minutes,
        refresh_token_ttl_days=config.backend.jwt_refresh_token_expire_days,
    )

    # -- Infrastructure: Messaging (Internal) --
    _notification_service = providers.Singleton(ConsoleNotificationService)

    # -- Persistence: Unit of Work (Internal) --
    _unit_of_work = providers.Factory(
        SQLAlchemyUnitOfWork,
        session_factory=_session_factory,
    )

    # -- Application Services (Exposed) --
    account_service = providers.Factory(
        AccountService,
        uow=_unit_of_work,
        password_hasher=_password_hasher,
        notification_service=_notification_service,
    )

    authentication_service = providers.Factory(
        AuthenticationService,
        uow=_unit_of_work,
        password_hasher=_password_hasher,
        token_service=_token_service,
    )
