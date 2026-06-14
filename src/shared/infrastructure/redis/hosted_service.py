import redis.asyncio as redis

from src.shared.infrastructure.di.hosted_service import HostedService
from src.shared.infrastructure.di.service_collection import ServiceCollection
from src.shared.infrastructure.redis.client import RedisClientFactory
from src.shared.infrastructure.redis.config import RedisSettings


class RedisHostedService(HostedService):
    """
    Manages the Redis connection DI registration and lifecycle.
    """

    def __init__(self, client: redis.Redis) -> None:
        self.client = client

    @classmethod
    def configure(cls, services: ServiceCollection) -> None:
        """Configures Redis DI bindings."""
        settings = RedisSettings()
        services.register(RedisSettings, settings)
        services.register(
            redis.Redis,
            lambda c: RedisClientFactory(c[RedisSettings])(),
        )
        services.register(cls, cls)

    async def start(self) -> None:
        """Pings Redis during boot to fail-fast if unreachable."""
        try:
            await self.client.ping()
        except Exception:
            raise RuntimeError("Could not connect to Redis")

    async def stop(self) -> None:
        """Closes the Redis connection pool on shutdown."""
        await self.client.close()
        await self.client.connection_pool.disconnect()
