from contextlib import asynccontextmanager
from typing import AsyncGenerator

from lagom import Container

from src.accounts.infrastructure.configuration.installer import AccountsServiceInstaller
from src.shared.infrastructure.di import HostBuilder
from src.shared.infrastructure.database import DatabaseHostedService
from src.shared.infrastructure.redis import RedisHostedService
from src.accounts.infrastructure.persistence.seeders.runner import AccountsSeederHostedService


@asynccontextmanager
async def bootstrap_application() -> AsyncGenerator[Container, None]:
    """
    Bootstrap the application by configuring services and establishing external
    resource connections.
    """
    builder = HostBuilder()

    # Add hosted services (they configure their own DI requirements internally)
    builder.services.add_hosted_service(DatabaseHostedService)
    builder.services.add_hosted_service(RedisHostedService)
    builder.services.add_hosted_service(AccountsSeederHostedService)

    # Run service installers
    builder.services.add_installer(AccountsServiceInstaller)

    # Build the container (executes lifecycle startups and post-build wiring)
    async with builder.build() as container:
        yield container
