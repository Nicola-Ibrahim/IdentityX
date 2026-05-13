from typing import Any, Self
from src.accounts.infrastructure.module import AccountModule

class AccountsStartUp:
    """Manages the lifecycle of the Accounts module."""
    def __init__(self) -> None:
        self._module: AccountModule | None = None

    def initialize(self, database: Any) -> Self:
        try:
            # database is a dependency_injector provider, call it to get the instance
            session_factory = database()
            self._module = AccountModule(session_factory)
            return self
        except Exception as ex:
            raise RuntimeError("Accounts module bootstrap failed") from ex

    async def stop(self) -> None:
        self._module = None

    @property
    def module(self) -> AccountModule | None:
        """Return the initialized AccountModule."""
        return self._module
