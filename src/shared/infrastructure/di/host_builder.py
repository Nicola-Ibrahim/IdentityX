from contextlib import asynccontextmanager
from typing import AsyncGenerator

from lagom import Container

from src.shared.infrastructure.di.service_collection import ServiceCollection


class HostBuilder:
    """
    HostBuilder replicates the behavior of C#'s HostApplicationBuilder.
    It contains a 'services' property (ServiceCollection) to configure DI and lifecycles,
    and a 'build()' method to compile the application and construct the container.
    """

    def __init__(self) -> None:
        self.services = ServiceCollection()

    @asynccontextmanager
    async def build(self) -> AsyncGenerator[Container, None]:
        """
        Builds the ServiceCollection DI container and executes lifecycles.
        """
        async with self.services.build() as container:
            yield container
