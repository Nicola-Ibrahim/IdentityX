from typing import Any

from ...accounts.application.interfaces.account_module import BaseAccountModule
from ...building_blocks.application.commands import BaseCommand
from ...building_blocks.application.queries import BaseQuery
from ...building_blocks.application.mediator import   , Mediator
from ...building_blocks.domain.result import Result


class AccountModule(BaseAccountModule):
    """
    Infrastructure implementation of the Account module.
    It encapsulates the Mediator and provides a clean entry point for the API layer.
    """

    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    @Result.capture
    async def execute(self, command: BaseCommand[Any]) -> Any:
        """Execute a command through the mediator."""
        return await self._mediator.execute(command)

    @Result.capture
    async def query(self, query: BaseQuery[Any]) -> Any:
        """Execute a query through the mediator."""
        return await self._mediator.query(query)
