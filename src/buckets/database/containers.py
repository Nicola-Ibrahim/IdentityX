from lagom import Container

from src.buckets.database.config import SQLAlchemySettings
from src.buckets.database.session import SQLAlchemySessionFactory


async def configure_db_dependencies(container: Container) -> None:
    """Initialize database session factory and register it to the global Container."""
    settings = SQLAlchemySettings()
    factory = SQLAlchemySessionFactory(settings)
    # Explicit connection check (Fail-Fast)
    if not await factory.ping():
        raise RuntimeError(f"Could not connect to Database at {settings.url}")

    container[SQLAlchemySettings] = settings
    container[SQLAlchemySessionFactory] = factory


async def shutdown_database(factory: SQLAlchemySessionFactory) -> None:
    """Shutdown database and dispose connections."""
    await factory.dispose()
