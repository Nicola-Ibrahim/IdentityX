import contextvars

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.buckets.database.config import SQLAlchemySettings

# 1. The Global Context Variable
# This acts as our safe, request-scoped container for the session.
_current_session: contextvars.ContextVar[AsyncSession] = contextvars.ContextVar("current_session")


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
        """Creates and returns a BRAND NEW session."""
        return self._session_factory()

    async def dispose(self) -> None:
        """Dispose the underlying engine and its connection pool."""
        await self._engine.dispose()

    async def ping(self) -> bool:
        """Verify the database connection."""
        try:
            from sqlalchemy import text

            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def get_current_session() -> AsyncSession:
        """
        Helper to grab the active session from the context variable.
        Repositories will call this method.
        """
        try:
            return _current_session.get()
        except LookupError:
            raise RuntimeError(
                "No active database session found in context. "
                "Ensure this code runs inside a TransactionScope (e.g. via TransactionBehavior in Mediator pipeline)."
            )
