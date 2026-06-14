from src.shared.infrastructure.di.hosted_service import HostedService
from src.shared.infrastructure.di.service_collection import ServiceCollection
from src.shared.infrastructure.database.config import SQLAlchemySettings
from src.shared.infrastructure.database.session import SQLAlchemySessionFactory


class DatabaseHostedService(HostedService):
    """
    Manages the Database connection DI registration and lifecycle.
    """

    def __init__(self, factory: SQLAlchemySessionFactory) -> None:
        self.factory = factory

    @classmethod
    def configure(cls, services: ServiceCollection) -> None:
        """Configures Database DI bindings."""
        settings = SQLAlchemySettings()
        services.register(SQLAlchemySettings, settings)
        services.register(
            SQLAlchemySessionFactory,
            lambda c: SQLAlchemySessionFactory(c[SQLAlchemySettings]),
        )
        services.register(cls, cls)

    async def start(self) -> None:
        """Pings the database during boot to fail-fast if unreachable."""
        if not await self.factory.ping():
            raise RuntimeError("Could not connect to Database")

    async def stop(self) -> None:
        """Disposes the database connection pool on shutdown."""
        await self.factory.dispose()
