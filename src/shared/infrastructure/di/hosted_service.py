class HostedService:
    """
    HostedService defines a lifecycle contract for background tasks,
    external connections, or startup/teardown logic.
    Replicates C#'s IHostedService interface.
    """

    async def start(self) -> None:
        """Executed on application startup."""
        pass

    async def stop(self) -> None:
        """Executed on application shutdown."""
        pass
