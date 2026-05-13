from typing import Any
from src.building_blocks.application.mediator import Mediator, BaseCommand, BaseQuery
from src.building_blocks.application.module import BaseModule
from src.building_blocks.domain.result import Result

from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.application.interfaces.password_hasher import BasePasswordHasher
from src.accounts.application.interfaces.jwt import TokenService
from src.accounts.application.interfaces.notification_service import BaseNotificationService
from src.accounts.domain.services.audit_service import AuditService

from src.accounts.infrastructure.persistence.repositories.account import SQLBaseAccountRepository
from src.accounts.infrastructure.persistence.repositories.session import SQLBaseSessionRepository
from src.accounts.infrastructure.persistence.repositories.audit import SQLAuditLogRepository
from src.accounts.infrastructure.crypto.password_hasher import PBKDF2PasswordHasher
from src.accounts.infrastructure.crypto.jwt_token import JWTTokenService
from src.accounts.infrastructure.messaging.email_notifier import ConsoleNotificationService
from src.accounts.infrastructure.configuration.settings import AccountsSettings
from src.accounts.application.providers import SocialProviders
from src.accounts.infrastructure.authentication.social.google_provider import GoogleAuthenticationProvider

from src.building_blocks.infrastructure.transaction import TransactionBehavior
from src.buckets.database.session import SQLAlchemySessionFactory

class AccountModule(BaseModule):
    """Main module for Accounts, handling dependency injection and Mediator delegation."""
    
    def __init__(self, session_factory: SQLAlchemySessionFactory):
        settings = AccountsSettings()
        
        transaction_behavior = TransactionBehavior(session_factory)
        
        # Instantiate Mediator with "src" root package for assembly scanning
        self._mediator = Mediator(root_package="src", behaviors=[transaction_behavior])
        
        # Register services
        self._mediator.register_service(BaseAccountRepository, lambda: SQLBaseAccountRepository())
        self._mediator.register_service(BaseSessionRepository, lambda: SQLBaseSessionRepository())
        self._mediator.register_service(BaseAuditRepository, lambda: SQLAuditLogRepository())
        
        self._mediator.register_service(BasePasswordHasher, lambda: PBKDF2PasswordHasher())
        
        token_service = JWTTokenService(
            private_key=settings.JWT_PRIVATE_KEY,
            public_key=settings.JWT_PUBLIC_KEY,
            algorithm=settings.JWT_ALGORITHM,
            issuer=settings.JWT_ISSUER,
            access_token_ttl_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_ttl_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        )
        self._mediator.register_service(TokenService, lambda: token_service)
        
        self._mediator.register_service(BaseNotificationService, lambda: ConsoleNotificationService())
        
        self._mediator.register_service(AuditService, lambda: AuditService(audit_repo=SQLAuditLogRepository()))
        
        google_provider = GoogleAuthenticationProvider(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
            auth_url=settings.GOOGLE_AUTH_URL,
            server_metadata_url=settings.GOOGLE_METADATA_URL,
        )
        
        social_providers = SocialProviders({"google": google_provider})
        self._mediator.register_service(SocialProviders, lambda: social_providers)

    @Result.capture
    async def execute(self, command: BaseCommand[Any]) -> Any:
        return await self._mediator.execute(command)

    @Result.capture
    async def query(self, query: BaseQuery[Any]) -> Any:
        return await self._mediator.query(query)
