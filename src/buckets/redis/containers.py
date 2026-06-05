import redis.asyncio as redis
from lagom import Container

from src.buckets.redis.client import RedisClientFactory
from src.buckets.redis.config import RedisSettings


async def configure_redis_dependencies(container: Container) -> None:
    """Initialize Redis client and register it to the global Container."""
    settings = RedisSettings()
    factory = RedisClientFactory(settings)
    client = factory()

    # Health check: Fail fast if Redis is unreachable
    if not await factory.ping():
        raise RuntimeError(f"Could not connect to Redis at {settings.REDIS_URL}")

    container[RedisSettings] = settings
    container[redis.Redis] = client


async def shutdown_redis(client: redis.Redis) -> None:
    """Shutdown Redis client connection pool."""
    if client:
        await client.close()
        await client.connection_pool.disconnect()
