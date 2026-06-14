from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.accounts.application.interfaces.notification_service import BaseNotificationService
from src.accounts.application.providers import SocialProviders
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.domain.account.services.password_hasher import PasswordHasher
from src.accounts.domain.audit.repositories.audit_repository import BaseAuditRepository
from src.accounts.domain.audit.services.audit_service import AuditService
from src.accounts.domain.session.repositories.session_repository import BaseSessionRepository
from src.accounts.domain.session.services.token_service import TokenService
from src.accounts.infrastructure.authentication.social.google_provider import GoogleAuthenticationProvider
from src.accounts.infrastructure.configuration.settings import AccountsSettings
from src.accounts.infrastructure.messaging.email_notifier import ConsoleNotificationService
from src.accounts.infrastructure.module import AccountModule
from src.accounts.infrastructure.persistence.repositories.account import SQLBaseAccountRepository
from src.accounts.infrastructure.persistence.repositories.audit import SQLAuditLogRepository
from src.accounts.infrastructure.persistence.repositories.session import SQLBaseSessionRepository
import redis.asyncio as redis
from src.accounts.infrastructure.persistence.caching.cached_session import CachedSessionRepository
from src.accounts.application.account.queries.list_accounts_query_service import ListAccountsQueryService
from src.accounts.infrastructure.persistence.queries.sql_list_accounts_query import SQLListAccountsQueryService
from src.shared.infrastructure.di import ServiceInstaller
from src.shared.infrastructure.di.service_collection import ServiceCollection
from src.shared.building_blocks.application.events import BaseEventBus
from src.shared.building_blocks.application.mediator import Mediator
from src.shared.infrastructure.database import SQLAlchemySessionFactory
from src.shared.infrastructure.database.transaction import TransactionBehavior
from src.shared.infrastructure.events import LocalEventBus


class AccountsServiceInstaller(ServiceInstaller):
    """
    Encapsulates all dependency injection registrations for the Accounts module.
    """

    def configure(self, services: ServiceCollection) -> None:
        # 1. Bind settings
        settings = AccountsSettings()
        services.register(AccountsSettings, settings)

        # 2. Bind Repositories
        services.register(BaseAccountRepository, SQLBaseAccountRepository)
        services.register(SQLBaseSessionRepository, SQLBaseSessionRepository)
        services.register(
            BaseSessionRepository,
            lambda c: CachedSessionRepository(
                database_repo=c[SQLBaseSessionRepository],
                redis_client=c[redis.Redis],
            ),
        )
        services.register(BaseAuditRepository, SQLAuditLogRepository)

        # 3. Bind Core Services
        services.register(PasswordHasher, PasswordHasher)
        services.register(BaseNotificationService, ConsoleNotificationService)
        services.register(AuditService, AuditService)

        # 4. Bind configured TokenService
        token_service = TokenService(
            private_key=settings.JWT_PRIVATE_KEY,
            public_key=settings.JWT_PUBLIC_KEY,
            algorithm=settings.JWT_ALGORITHM,
            issuer=settings.JWT_ISSUER,
            access_token_ttl_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_ttl_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        )
        services.register(TokenService, token_service)

        # 5. Bind Social Auth Providers
        google_provider = GoogleAuthenticationProvider(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=str(settings.GOOGLE_REDIRECT_URI),
            auth_url=str(settings.GOOGLE_AUTH_URL),
            server_metadata_url=str(settings.GOOGLE_METADATA_URL),
        )
        services.register(SocialProviders, SocialProviders(providers={"google": google_provider}))

        # 6. Bind container-dependent components lazily using container lambdas
        services.register(BaseEventBus, lambda c: LocalEventBus(container=c))
        
        services.register(
            Mediator,
            lambda c: Mediator(
                container=c,
                behaviors=[TransactionBehavior(session_factory=c[SQLAlchemySessionFactory])],
            ),
        )

        services.register(ListAccountsQueryService, SQLListAccountsQueryService)
        services.register(BaseAccountModule, lambda c: AccountModule(c[Mediator]))
