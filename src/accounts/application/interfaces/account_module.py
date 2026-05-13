from abc import abstractmethod
from typing import Any

from ....building_blocks.application.commands import BaseCommand
from ....building_blocks.application.queries import BaseQuery
from ....building_blocks.application.module import BaseModule


class BaseAccountModule(BaseModule):
    """
    Interface for the Account module in the application layer.
    """

    @abstractmethod
    async def execute(self, command: BaseCommand[Any]) -> Any:
        """Execute a command through the module."""
        raise NotImplementedError

    @abstractmethod
    async def query(self, query: BaseQuery[Any]) -> Any:
        """Execute a query through the module."""
        raise NotImplementedError
