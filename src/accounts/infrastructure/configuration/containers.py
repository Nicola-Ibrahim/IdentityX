from dependency_injector import containers, providers

from src.accounts.infrastructure.configuration.settings import AccountsSettings
from src.accounts.infrastructure.persistence.repositories.account import SQLBaseAccountRepository
from src.accounts.infrastructure.persistence.repositories.session import SQLBaseSessionRepository
from src.accounts.infrastructure.persistence.repositories.audit import SQLAuditLogRepository
from src.accounts.infrastructure.crypto.password_hasher import PBKDF2PasswordHasher
from src.accounts.infrastructure.crypto.jwt_token import JWTTokenService
from src.accounts.infrastructure.messaging.email_notifier import ConsoleNotificationService
from src.accounts.infrastructure.authentication.social.google_provider import GoogleAuthenticationProvider
from src.accounts.application.providers import SocialProviders
from src.accounts.domain.services.audit_service import AuditService

class AccountsContainer(containers.DeclarativeContainer):
    """Infrastructure-level DI container for the Accounts module."""
    
    settings = providers.Singleton(AccountsSettings)
    
    # Repositories
    account_repository = providers.Factory(SQLBaseAccountRepository)
    session_repository = providers.Factory(SQLBaseSessionRepository)
    audit_repository = providers.Factory(SQLAuditLogRepository)
    
    # Services
    password_hasher = providers.Factory(PBKDF2PasswordHasher)
    
    token_service = providers.Singleton(
        JWTTokenService,
        private_key=settings.provided.JWT_PRIVATE_KEY,
        public_key=settings.provided.JWT_PUBLIC_KEY,
        algorithm=settings.provided.JWT_ALGORITHM,
        issuer=settings.provided.JWT_ISSUER,
        access_token_ttl_minutes=settings.provided.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_ttl_days=settings.provided.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    )
    
    notification_service = providers.Factory(ConsoleNotificationService)
    
    audit_service = providers.Factory(
        AuditService,
        audit_repo=audit_repository
    )
    
    # Social Auth
    google_provider = providers.Singleton(
        GoogleAuthenticationProvider,
        client_id=settings.provided.GOOGLE_CLIENT_ID,
        client_secret=settings.provided.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.provided.GOOGLE_REDIRECT_URI,
        auth_url=settings.provided.GOOGLE_AUTH_URL,
        server_metadata_url=settings.provided.GOOGLE_METADATA_URL,
    )
    
    social_providers = providers.Singleton(
        SocialProviders,
        providers=providers.Dict({
            "google": google_provider
        })
    )
