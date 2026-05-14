from pydantic import BaseModel

from building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.application.dtos.account import AccountDTO


class ListAccountsQuery(BaseQuery[tuple[tuple[AccountDTO, ...], int]], BaseModel):
    limit: int = 100
    offset: int = 0


class ListAccountsHandler(BaseQueryHandler[ListAccountsQuery, tuple[tuple[AccountDTO, ...], int]]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, query: ListAccountsQuery) -> tuple[tuple[AccountDTO, ...], int]:
        accounts_iter, total_count = await self._account_repo.list_accounts(limit=query.limit, offset=query.offset)
        accounts = [AccountDTO.from_domain(account) for account in accounts_iter]
        return tuple(accounts), total_count
