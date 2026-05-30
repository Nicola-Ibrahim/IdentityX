from abc import ABC, abstractmethod


class BaseNotification:
    """Base class for all notifications/events."""

    pass


class BaseNotificationHandler[TNotification: BaseNotification](ABC):
    """Base class for all notification handlers."""

    @abstractmethod
    async def handle(self, notification: TNotification) -> None:
        raise NotImplementedError
