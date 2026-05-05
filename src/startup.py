from typing import Self

from .accounts.infrastructure.configuration.startup import AccountsStartUp
from .api.core.config import get_settings
from .buckets.database import DatabaseContainer
from .buckets.redis import RedisContainer


class IdentityXStartUp:
    """
    Orchestrates the initialization and teardown of all system modules
    and shared infrastructure.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._db_container = DatabaseContainer()
        self._redis_container = RedisContainer()
        self._accounts = AccountsStartUp()

        # List of all modules for easier iteration during init/stop
        self._modules = [self._accounts]

    @property
    def accounts(self) -> AccountsStartUp:
        return self._accounts

    @property
    def redis_container(self) -> RedisContainer:
        return self._redis_container

    async def initialize(self) -> Self:
        """
        Initialize all modules and shared infrastructure.
        """
        # 1. Initialize shared infrastructure resources
        await self._db_container.init_resources()
        await self._redis_container.init_resources()

        # 2. Initialize all modules
        for module in self._modules:
            module.initialize(database=self._db_container.session_factory)

        return self

    async def stop(self) -> None:
        """
        Stop all modules and clean up resources in reverse order.
        """
        for module in reversed(self._modules):
            await module.stop()

        # 3. Shutdown Redis infrastructure
        await self._redis_container.shutdown_resources()

        # 4. Shutdown shared database infrastructure
        await self._db_container.shutdown_resources()
