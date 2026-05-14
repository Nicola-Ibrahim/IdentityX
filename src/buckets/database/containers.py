from dependency_injector import containers, providers

from .config import SQLAlchemySettings
from .session import SQLAlchemySessionFactory


class DatabaseContainer(containers.DeclarativeContainer):
    """Container for database-related infrastructure."""

    settings = providers.Singleton(SQLAlchemySettings)

    @staticmethod
    async def _init_session_factory(settings: SQLAlchemySettings):
        factory = SQLAlchemySessionFactory(settings)
        # Explicit connection check (Fail-Fast)
        if not await factory.ping():
            raise RuntimeError(f"Could not connect to Database at {settings.url}")

        yield factory
        await factory.dispose()

    session_factory = providers.Resource(
        _init_session_factory,
        settings=settings,
    )
