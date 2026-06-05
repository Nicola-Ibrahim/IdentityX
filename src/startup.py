from typing import Self

from lagom import Container
from redis.asyncio import Redis

from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.accounts.infrastructure.configuration.containers import configure_accounts_dependencies
from src.buckets.database import (
    SQLAlchemySessionFactory,
    configure_db_dependencies,
    shutdown_database,
)
from src.buckets.redis import configure_redis_dependencies, shutdown_redis


class IdentityXStartUp:
    """
    The Composition Root. Orchestrates the initialization and teardown
    of all system modules and shared infrastructure using a single global Container.
    """

    def __init__(self) -> None:
        self.container = Container()

    @property
    def accounts(self) -> BaseAccountModule:
        """Return the Accounts module facade."""
        return self.container[BaseAccountModule]

    @property
    def session_factory(self) -> SQLAlchemySessionFactory:
        """Return the database session factory."""
        return self.container[SQLAlchemySessionFactory]

    async def initialize(self) -> Self:
        """Initialize all modules and shared infrastructure."""

        # 1. Initialize shared infrastructure resources
        await configure_db_dependencies(self.container)

        await configure_redis_dependencies(self.container)

        # 2. Initialize modules
        await configure_accounts_dependencies(self.container)

        return self

    async def stop(self) -> None:
        """Stop all modules and clean up resources."""

        # Shutdown Redis infrastructure
        redis_client = self.container[Redis]
        await shutdown_redis(redis_client)

        # Shutdown shared database infrastructure
        session_factory = self.container[SQLAlchemySessionFactory]
        await shutdown_database(session_factory)
