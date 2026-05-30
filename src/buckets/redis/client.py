import redis.asyncio as redis

from src.buckets.redis.config import RedisSettings


class RedisClientFactory:
    """
    Production-grade Factory for managing asynchronous Redis connections.
    Includes connection pooling, health checks, and graceful teardown.
    """

    def __init__(self, settings: RedisSettings) -> None:
        self._client = redis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            retry_on_timeout=True,
        )

    def __call__(self) -> redis.Redis:
        """
        Returns the initialized Redis client.
        """
        return self._client

    async def ping(self) -> bool:
        """
        Perform a health check on the Redis connection.
        Useful during application startup to fail fast if Redis is down.
        """
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        """
        Gracefully close the Redis connection pool.
        Ensures all connections are returned and closed.
        """
        if self._client:
            await self._client.close()
            # Wait for the pool to disconnect
            await self._client.connection_pool.disconnect()
            self._client = None
