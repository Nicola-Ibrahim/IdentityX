from typing import Any, Self, get_type_hints
from src.building_blocks.application.mediator import Mediator
from src.building_blocks.infrastructure.transaction import TransactionBehavior
from src.accounts.infrastructure.module import AccountModule
from src.accounts.infrastructure.configuration.containers import AccountsContainer

# Interfaces for registration
from src.accounts.domain.interfaces.account_repository import BaseAccountRepository
from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.interfaces.audit_repository import BaseAuditRepository
from src.accounts.application.interfaces.password_hasher import BasePasswordHasher
from src.accounts.application.interfaces.jwt import TokenService
from src.accounts.application.interfaces.notification_service import BaseNotificationService
from src.accounts.domain.services.audit_service import AuditService
from src.accounts.application.providers import SocialProviders

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
            session_factory = database()
            
            # 2. Define the Service Registry (Mapping Interfaces -> Infrastructure Providers)
            # This is the "C# Registration" equivalent
            service_map = {
                BaseAccountRepository: self._container.account_repository,
                BaseSessionRepository: self._container.session_repository,
                BaseAuditRepository: self._container.audit_repository,
                BasePasswordHasher: self._container.password_hasher,
                TokenService: self._container.token_service,
                BaseNotificationService: self._container.notification_service,
                AuditService: self._container.audit_service,
                SocialProviders: self._container.social_providers,
            }

            # 3. Create the Service Provider (Resolver) for the Mediator
            def service_provider(cls: type) -> Any:
                # If the requested type is a registered service, resolve it from the container
                if cls in service_map:
                    return service_map[cls]()
                
                # If it's a Handler class (or any other class), resolve its dependencies from the container
                if hasattr(cls, "__init__"):
                    hints = get_type_hints(cls.__init__)
                    kwargs = {}
                    for name, hint in hints.items():
                        if name == "return":
                            continue
                        kwargs[name] = service_provider(hint)
                    return cls(**kwargs)
                
                raise LookupError(f"Cannot resolve dependency of type: {cls.__name__}")

            # 4. Configure the Mediator
            # Scan for all handlers in the project
            Mediator.scan("src")
            
            mediator = Mediator(
                service_provider=service_provider,
                behaviors=[TransactionBehavior(session_factory)]
            )
            
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
