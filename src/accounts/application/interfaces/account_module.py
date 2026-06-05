from abc import abstractmethod

from src.building_blocks.application.mediator import BaseCommand, BaseQuery
from src.building_blocks.application.module import BaseModule
from src.building_blocks.domain.result import Result


class BaseAccountModule(BaseModule):
    """
    Interface for the Account module in the application layer.
    """

    @abstractmethod
    async def execute[TResponse](self, command: BaseCommand[TResponse]) -> Result[TResponse, Exception]:
        """Execute a command through the module."""
        raise NotImplementedError

    @abstractmethod
    async def query[TResponse](self, query: BaseQuery[TResponse]) -> Result[TResponse, Exception]:
        """Execute a query through the module."""
        raise NotImplementedError
