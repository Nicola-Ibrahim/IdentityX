from typing import Self

from src.accounts.infrastructure.configuration.startup import AccountsStartUp
from src.api.core.config import get_settings
from src.buckets.database import DatabaseContainer
from src.buckets.redis import RedisContainer


class IdentityXStartUp:
    """
    The Composition Root. Orchestrates the initialization and teardown
    of all system modules and shared infrastructure.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._db_container = DatabaseContainer()
        self._redis_container = RedisContainer()

        # This handles the AccountsDIContainer internally
        self._accounts = AccountsStartUp()

        # List of all modules for easier iteration during init/stop
        self._modules = [self._accounts]

    @property
    def accounts(self) -> AccountsStartUp:
        return self._accounts

    @property
    def redis_container(self) -> RedisContainer:
        return self._redis_container

    @property
    def session_factory(self):
        return self._db_container.session_factory()

    async def initialize(self) -> Self:
        """Initialize all modules and shared infrastructure."""

        # 1. Initialize shared infrastructure resources
        db_res = self._db_container.init_resources()
        if db_res:
            await db_res

        redis_res = self._redis_container.init_resources()
        if redis_res:
            await redis_res

        # 2. Initialize all modules
        for module in self._modules:
            module.initialize(database=self._db_container.session_factory)

        return self

    async def stop(self) -> None:
        """Stop all modules and clean up resources in reverse order."""
        for module in reversed(self._modules):
            await module.stop()

        # Shutdown Redis infrastructure
        redis_res = self._redis_container.shutdown_resources()
        if redis_res:
            await redis_res

        # Shutdown shared database infrastructure
        db_res = self._db_container.shutdown_resources()
        if db_res:
            await db_res
