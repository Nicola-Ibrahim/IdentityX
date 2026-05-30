import unittest
from typing import override
from src.building_blocks.application.mediator import (
    BaseNotification,
    BaseNotificationHandler,
    Mediator,
    ServiceContainer,
)

# Global tracker for testing handler execution
called_handlers: list[tuple[str, str]] = []


class UserRegisteredEvent(BaseNotification):
    def __init__(self, email: str) -> None:
        self.email = email


class SendWelcomeEmailHandler(BaseNotificationHandler[UserRegisteredEvent]):
    @override
    async def handle(self, notification: UserRegisteredEvent) -> None:
        called_handlers.append(("SendWelcomeEmailHandler", notification.email))


class LogUserRegistrationHandler(BaseNotificationHandler[UserRegisteredEvent]):
    @override
    async def handle(self, notification: UserRegisteredEvent) -> None:
        called_handlers.append(("LogUserRegistrationHandler", notification.email))


class TestMediatorNotifications(unittest.IsolatedAsyncioTestCase):
    async def test_publish_notification_calls_all_handlers(self) -> None:
        called_handlers.clear()

        container = ServiceContainer()
        mediator = Mediator(container=container)

        event = UserRegisteredEvent(email="test@example.com")
        await mediator.publish(event)

        self.assertEqual(len(called_handlers), 2)
        self.assertIn(("SendWelcomeEmailHandler", "test@example.com"), called_handlers)
        self.assertIn(("LogUserRegistrationHandler", "test@example.com"), called_handlers)

    async def test_publish_notification_with_no_handlers(self) -> None:
        class SomeUnregisteredEvent(BaseNotification):
            pass

        container = ServiceContainer()
        mediator = Mediator(container=container)

        # This should run and succeed silently without raising any exceptions
        await mediator.publish(SomeUnregisteredEvent())
