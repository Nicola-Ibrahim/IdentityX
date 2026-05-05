from dependency_injector import containers, providers

from .config import SQLAlchemySettings
from .session import SQLAlchemySessionFactory


class DatabaseContainer(containers.DeclarativeContainer):
    """Container for database-related infrastructure."""

    settings = providers.Singleton(SQLAlchemySettings)

    @staticmethod
    async def _init_session_factory(settings: SQLAlchemySettings):
        factory = SQLAlchemySessionFactory(settings)
        yield factory
        await factory.dispose()

    session_factory = providers.Resource(
        _init_session_factory,
        settings=settings,
    )
