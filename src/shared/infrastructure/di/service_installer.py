from src.shared.infrastructure.di.service_collection import ServiceCollection


class ServiceInstaller:
    """
    ServiceInstaller defines an encapsulation unit for registering dependencies
    and configuring lifecycles.
    Replicates C#'s service installer pattern.
    """

    def configure(self, services: ServiceCollection) -> None:
        """Configure registrations and add hosted services."""
        pass
