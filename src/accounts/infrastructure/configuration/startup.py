from typing import Any, Self

from src.accounts.domain.services.token_service import TokenService
from src.accounts.application.interfaces.notification_service import BaseNotificationService
from src.accounts.domain.services.password_hasher import PasswordHasher
from src.accounts.application.providers import SocialProviders

# Interfaces for registration
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.services.audit_service import AuditService
from src.accounts.infrastructure.configuration.containers import AccountsContainer
from src.accounts.infrastructure.module import AccountModule
from src.buckets.database.transaction import TransactionBehavior
from src.building_blocks.application.mediator import Mediator, ServiceContainer
from src.building_blocks.application.events import BaseEventBus
from src.building_blocks.infrastructure.events import LocalEventBus


class AccountsStartUp:
    """
    Handles the initialization of the Accounts module, wiring the DI container
    with the Mediator, EventBus, and the Facade.

    Separation of concerns:
      - ``Mediator``     → Application CQRS (Commands + Queries, 1-to-1).
      - ``EventBus``     → Domain event dispatching (1-to-many).  The concrete
                           ``LocalEventBus`` can be swapped for a broker-backed
                           implementation by changing only this file.
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
            container.register(BaseAuditRepository, self._container.audit_repository)
            container.register(PasswordHasher, self._container.password_hasher)
            container.register(TokenService, self._container.token_service)
            container.register(BaseNotificationService, self._container.notification_service)
            container.register(AuditService, self._container.audit_service)
            container.register(SocialProviders, self._container.social_providers)

            # Resolve the database session factory from the passed DB container/factory
            session_factory = database()

            # 3. Configure Event Bus (Domain Events, 1-to-many)
            event_bus = LocalEventBus(container=container)
            container.register(BaseEventBus, lambda: event_bus)

            # 4. Set up transaction behaviors wrapping commands
            behaviors = [
                TransactionBehavior(session_factory=session_factory),
            ]

            # 5. Configure the CQRS Mediator (Commands + Queries only)
            mediator = Mediator(container=container, behaviors=behaviors)
            container.register(Mediator, lambda: mediator)

            # 6. Wire repositories (pure persistence)
            container.register(
                BaseAccountRepository,
                lambda: self._container.account_repository(),
            )
            container.register(
                BaseSessionRepository,
                lambda: self._container.session_repository(),
            )

            # 7. Initialize the Facade (AccountModule)
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
