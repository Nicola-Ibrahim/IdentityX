from lagom import Container

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
from src.buckets.database import SQLAlchemySessionFactory
from src.buckets.database.transaction import TransactionBehavior
from src.building_blocks.application.events import BaseEventBus
from src.building_blocks.application.mediator import Mediator
from src.building_blocks.infrastructure.events import LocalEventBus


async def configure_accounts_dependencies(container: Container) -> None:
    """Configure dependency bindings for the Accounts module directly in the global Container."""
    # 1. Bind settings
    settings = AccountsSettings()
    container[AccountsSettings] = settings

    # 2. Bind Repositories
    container[BaseAccountRepository] = SQLBaseAccountRepository
    container[BaseSessionRepository] = SQLBaseSessionRepository
    container[BaseAuditRepository] = SQLAuditLogRepository

    # 3. Bind Core Services
    container[PasswordHasher] = PasswordHasher
    container[BaseNotificationService] = ConsoleNotificationService
    container[AuditService] = AuditService

    # 4. Bind configured TokenService
    token_service = TokenService(
        private_key=settings.JWT_PRIVATE_KEY,
        public_key=settings.JWT_PUBLIC_KEY,
        algorithm=settings.JWT_ALGORITHM,
        issuer=settings.JWT_ISSUER,
        access_token_ttl_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_ttl_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    container[TokenService] = token_service

    # 5. Bind Social Auth Providers
    google_provider = GoogleAuthenticationProvider(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=str(settings.GOOGLE_REDIRECT_URI),
        auth_url=str(settings.GOOGLE_AUTH_URL),
        server_metadata_url=str(settings.GOOGLE_METADATA_URL),
    )
    container[SocialProviders] = SocialProviders(providers={"google": google_provider})

    # 6. Bind Event Bus
    event_bus = LocalEventBus(container=container)
    container[BaseEventBus] = event_bus

    # 7. Bind Infrastructure (Mediator)
    session_factory = container[SQLAlchemySessionFactory]
    behaviors = [
        TransactionBehavior(session_factory=session_factory),
    ]
    mediator = Mediator(container=container, behaviors=behaviors)
    container[Mediator] = mediator

    # Bind Module Facade
    container[BaseAccountModule] = lambda c: AccountModule(c[Mediator])
