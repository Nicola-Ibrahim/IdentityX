from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncGenerator, List, Type

from lagom import Container

from src.shared.infrastructure.di.hosted_service import HostedService


class ServiceCollection:
    """
    ServiceCollection acts as a builder for configuring and assembling
    dependency injection registrations and resource lifecycles.

    Replicates the behavior of IServiceCollection in C#, supporting:
    1. Synchronous DI registrations directly into a Lagom Container.
    2. HostedService lifecycles for connections/background processes.
    3. Modular configuration packaging via ServiceInstallers.
    """

    def __init__(self) -> None:
        self._container = Container()
        self._hosted_services: List[Type[HostedService]] = []

    def register(self, abstract: Any, concrete: Any) -> None:
        """
        Maps an abstract class or type to its concrete implementation.
        """
        self._container[abstract] = concrete

    def add_hosted_service(self, service_type: Type[HostedService]) -> None:
        """
        Registers a HostedService class in DI and tracks it for execution
        during application startup/teardown.
        """
        if hasattr(service_type, "configure") and callable(getattr(service_type, "configure")):
            service_type.configure(self)
        else:
            self.register(service_type, service_type)
        self._hosted_services.append(service_type)

    def add_installer(self, installer_type: Type[Any]) -> None:
        """
        Instantiates the installer and invokes its configure method to append its dependencies and lifecycles.
        """
        installer = installer_type()
        installer.configure(self)

    @asynccontextmanager
    async def build(self) -> AsyncGenerator[Container, None]:
        """
        Resolves and starts all registered HostedServices, then yields the
        fully configured Lagom Container. Handles clean shutdown of lifecycles.
        """
        async with AsyncExitStack() as stack:
            # Resolve all registered hosted services and manage their lifecycles
            for service_type in self._hosted_services:
                service = self._container[service_type]

                # Helper to convert start/stop methods to an async context manager
                async def _lifecycle_wrapper(srv: HostedService) -> AsyncGenerator[None, None]:
                    await srv.start()
                    try:
                        yield
                    finally:
                        await srv.stop()

                # Call enter_async_context to register start/stop with the ExitStack
                await stack.enter_async_context(asynccontextmanager(_lifecycle_wrapper)(service))

            yield self._container
