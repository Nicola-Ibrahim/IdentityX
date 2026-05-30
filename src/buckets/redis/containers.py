from dependency_injector import containers, providers
from src.buckets.redis.client import RedisClientFactory
from src.buckets.redis.config import RedisSettings


class RedisContainer(containers.DeclarativeContainer):
    """Container for Redis-related infrastructure."""

    settings = providers.Singleton(RedisSettings)

    @staticmethod
    async def _init_redis_client(settings: RedisSettings):
        factory = RedisClientFactory(settings)
        client = factory()

        # Health check: Fail fast if Redis is unreachable
        if not await factory.ping():
            raise RuntimeError(f"Could not connect to Redis at {settings.REDIS_URL}")

        yield client
        await factory.close()

    client = providers.Resource(
        _init_redis_client,
        settings=settings,
    )
