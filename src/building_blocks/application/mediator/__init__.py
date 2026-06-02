"""
IdentityX Mediator — Application CQRS Dispatcher.

This module provides a lightweight, in-process Mediator for **Commands** and
**Queries** only (strict 1-to-1 dispatch).

Domain event dispatching (1-to-many) is handled by the EventBus:
  - Abstract contract : ``building_blocks.application.events.BaseEventBus``
  - In-memory impl   : ``building_blocks.infrastructure.events.LocalEventBus``

Folder Structure:
    - core/       : Framework engine (Mediator, ServiceContainer, Behaviors, Exceptions)
    - messages/   : Message primitives and handler contracts (Commands, Queries)

Usage Examples:

    1. Defining and Handling a Command::

        from src.building_blocks.application.mediator import (
            BaseCommand,
            BaseCommandHandler,
        )

        class RegisterUserCommand(BaseCommand[int]):
            username: str

        class RegisterUserCommandHandler(BaseCommandHandler[RegisterUserCommand, int]):
            async def handle(self, command: RegisterUserCommand) -> int:
                return 42

    2. Executing with the Mediator::

        from src.building_blocks.application.mediator import Mediator, ServiceContainer

        container = ServiceContainer()
        mediator  = Mediator(container=container)
        user_id   = await mediator.execute(RegisterUserCommand(username="alice"))

    3. Defining and Handling a Query::

        from src.building_blocks.application.mediator import BaseQuery, BaseQueryHandler

        class GetUserQuery(BaseQuery[UserDto]):
            user_id: int

        class GetUserQueryHandler(BaseQueryHandler[GetUserQuery, UserDto]):
            async def handle(self, query: GetUserQuery) -> UserDto:
                ...
"""

from src.building_blocks.application.mediator.core.mediator import Mediator
from src.building_blocks.application.mediator.core.provider import ServiceContainer
from src.building_blocks.application.mediator.core.behaviors import BaseBehavior
from src.building_blocks.application.mediator.core.exceptions import MediatorError, HandlerNotFoundError

from src.building_blocks.application.mediator.messages.commands import BaseCommand, BaseCommandHandler
from src.building_blocks.application.mediator.messages.queries import BaseQuery, BaseQueryHandler

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
]
