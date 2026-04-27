from .entity import Entity, TEntityId


class AggregateRoot(Entity[TEntityId]):
    """Aggregate root marker that extends :class:`Entity`."""

    def mark_committed(self) -> None:
        """
        Clear pending events after they have been dispatched.
        This provides a semantic alias over :meth:`Entity.pull_events`.
        """
        self.pull_events()
