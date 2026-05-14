from abc import abstractmethod
from typing import Generic, TypeVar

TResponse = TypeVar("TResponse")
TCommand = TypeVar("TCommand", bound="BaseCommand")


class BaseCommand(Generic[TResponse]):
    """Base class for all commands."""

    pass


class BaseCommandHandler(Generic[TCommand, TResponse]):
    """Base class for all command handlers."""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResponse:
        raise NotImplementedError
