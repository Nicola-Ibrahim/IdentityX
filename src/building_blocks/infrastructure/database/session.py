from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


from .config import SQLAlchemySettings


class SQLAlchemySessionFactory:
    """Factory for managing asynchronous SQLAlchemy sessions."""

    def __init__(self, config: SQLAlchemySettings) -> None:
        self._engine = create_async_engine(
            config.url,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_recycle=config.pool_recycle,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def __call__(self) -> AsyncSession:
        return self._session_factory()

    async def dispose(self) -> None:
        """Dispose the underlying engine and its connection pool."""
        await self._engine.dispose()
