from abc import ABC, abstractmethod


class BaseCommand[TResponse]:
    """Base class for all commands."""

    pass


class BaseCommandHandler[TCommand: BaseCommand, TResponse](ABC):
    """Base class for all command handlers."""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResponse:
        raise NotImplementedError
