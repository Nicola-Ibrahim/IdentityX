from typing import Any, Self

from accounts.application.interfaces.jwt import TokenService
from accounts.application.interfaces.notification_service import BaseNotificationService
from accounts.application.interfaces.password_hasher import BasePasswordHasher
from accounts.application.providers import SocialProviders

# Interfaces for registration
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.domain.interfaces.audit_repository import BaseAuditRepository
from accounts.domain.interfaces.session_repository import BaseSessionRepository
from accounts.domain.services.audit_service import AuditService
from accounts.infrastructure.configuration.containers import AccountsContainer
from accounts.infrastructure.module import AccountModule
from buckets.database.transaction import TransactionBehavior
from building_blocks.application.mediator import Mediator, ServiceContainer


class AccountsStartUp:
    """
    Handles the initialization of the Accounts module, wiring the DI container
    with the Mediator and the Facade.
    """

    def __init__(self) -> None:
        self._module: AccountModule | None = None
        self._container: AccountsContainer | None = None

    def initialize(self, database: Any) -> Self:
        try:
            # 1. Initialize the Infrastructure Container
            self._container = AccountsContainer()

            # 2. Create the ServiceContainer and register dependencies
            container = ServiceContainer()
            container.register(BaseAccountRepository, self._container.account_repository)
            container.register(BaseSessionRepository, self._container.session_repository)
            container.register(BaseAuditRepository, self._container.audit_repository)
            container.register(BasePasswordHasher, self._container.password_hasher)
            container.register(TokenService, self._container.token_service)
            container.register(BaseNotificationService, self._container.notification_service)
            container.register(AuditService, self._container.audit_service)
            container.register(SocialProviders, self._container.social_providers)

            # Resolve the database session factory from the passed DB container/factory
            session_factory = database()

            # Set up transaction behavior wrapping commands
            behaviors = [TransactionBehavior(session_factory=session_factory)]

            # 4. Configure the localized Mediator
            mediator = Mediator(container=container, behaviors=behaviors)

            # 5. Initialize the Facade (AccountModule)
            self._module = AccountModule(mediator)

            return self
        except Exception as ex:
            raise RuntimeError("Accounts module bootstrap failed") from ex

    async def stop(self) -> None:
        self._module = None
        self._container = None

    @property
    def module(self) -> AccountModule | None:
        """Return the initialized AccountModule facade."""
        return self._module
