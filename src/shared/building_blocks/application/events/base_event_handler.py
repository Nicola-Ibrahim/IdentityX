from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.shared.building_blocks.domain.events import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)


class BaseEventHandler(ABC, Generic[TEvent]):
    """
    Abstract base for a domain event handler.

    Each concrete handler is responsible for exactly one event type ``TEvent``.
    The ``LocalEventBus`` (and any other implementation) auto-discovers concrete
    subclasses by inspecting the generic type parameter, so no manual registration
    is required — simply create the class and the bus will find it.

    Example::

        class SendWelcomeEmailHandler(BaseEventHandler[AccountRegisteredEvent]):
            def __init__(self, notification_service: BaseNotificationService) -> None:
                self._notifications = notification_service

            async def handle(self, event: AccountRegisteredEvent) -> None:
                await self._notifications.send_welcome(event.email)
    """

    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        """Process the domain event."""
        ...
