from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.shared.building_blocks.application.mediator import BaseCommand, BaseQuery, Mediator
from src.shared.building_blocks.domain.result import Result


class AccountModule(BaseAccountModule):
    """
    Infrastructure implementation of the Account module.
    It encapsulates the Mediator and provides a clean entry point for the API layer.
    """

    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    async def execute[TResponse](self, command: BaseCommand[TResponse]) -> Result[TResponse, Exception]:
        """Execute a command through the mediator."""
        try:
            value = await self._mediator.execute(command)
            return Result.success(value)
        except Exception as e:
            return Result.fail(e)

    async def query[TResponse](self, query: BaseQuery[TResponse]) -> Result[TResponse, Exception]:
        """Execute a query through the mediator."""
        try:
            value = await self._mediator.query(query)
            return Result.success(value)
        except Exception as e:
            return Result.fail(e)

