"""
IdentityX Mediator Pattern Implementation.

This module provides a lightweight, localized, in-process Mediator implementation
heavily inspired by the MediatR library in C#/.NET. It decouples the sending of
messages (Commands, Queries, Notifications) from their execution handlers,
supporting middleware behaviors (pipeline processing) for cross-cutting concerns
such as logging, validation, and transaction management.

Folder Structure:
    - core/       : Framework engine (Mediator, ServiceContainer, Behaviors, Exceptions)
    - messages/   : Message primitives and base handler contracts (Commands, Queries, Notifications)

Core Primitives:
    1. Commands: Write operations representing actions that modify system state. Returns a response.
    2. Queries: Read operations representing data requests with no side effects. Returns data.
    3. Notifications: One-to-many event messages dispatched to multiple handlers. Returns nothing.

Usage Examples:

    1. Defining and Handling a Command:
        >>> from building_blocks.application.mediator import BaseCommand, BaseCommandHandler
        >>>
        >>> class RegisterUserCommand(BaseCommand[int]):
        ...     def __init__(self, username: str) -> None:
        ...         self.username = username
        >>>
        >>> class RegisterUserCommandHandler(BaseCommandHandler[RegisterUserCommand, int]):
        ...     async def handle(self, command: RegisterUserCommand) -> int:
        ...         # Business logic to register user
        ...         return 42

    2. Registering and Executing with the Mediator:
        >>> from building_blocks.application.mediator import Mediator, ServiceContainer
        >>>
        >>> container = ServiceContainer()
        >>> container.register(RegisterUserCommandHandler, lambda: RegisterUserCommandHandler())
        >>>
        >>> mediator = Mediator(container)
        >>> user_id = await mediator.execute(RegisterUserCommand("john_doe"))

    3. Dispatching Notifications (Events):
        >>> from building_blocks.application.mediator import BaseNotification, BaseNotificationHandler
        >>>
        >>> class UserCreatedNotification(BaseNotification):
        ...     def __init__(self, user_id: int) -> None:
        ...         self.user_id = user_id
        >>>
        >>> class SendWelcomeEmailHandler(BaseNotificationHandler[UserCreatedNotification]):
        ...     async def handle(self, notification: UserCreatedNotification) -> None:
        ...         print(f"Sending welcome email to user {notification.user_id}")
        >>>
        >>> # Publish will execute all matching notification handlers sequentially
        >>> await mediator.publish(UserCreatedNotification(42))
"""

from .core.mediator import Mediator
from .core.provider import ServiceContainer
from .core.behaviors import BaseBehavior
from .core.exceptions import MediatorError, HandlerNotFoundError

from .messages.commands import BaseCommand, BaseCommandHandler
from .messages.queries import BaseQuery, BaseQueryHandler
from .messages.notifications import BaseNotification, BaseNotificationHandler

__all__ = [
    "Mediator",
    "ServiceContainer",
    "BaseBehavior",
    "MediatorError",
    "HandlerNotFoundError",
    "BaseCommand",
    "BaseCommandHandler",
    "BaseQuery",
    "BaseQueryHandler",
    "BaseNotification",
    "BaseNotificationHandler",
]
