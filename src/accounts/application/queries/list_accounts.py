from pydantic import BaseModel

from ....building_blocks.application.queries import BaseQuery
from ....building_blocks.application.mediator import BaseQuery,  Handler
from ...domain.interfaces.account_repository import BaseAccountRepository
from ..dtos.account import AuthDTO


class ListAccountsQuery(BaseQuery[tuple[tuple[AuthDTO, ...], int]], BaseModel):
    limit: int = 100
    offset: int = 0


class ListAccountsHandler(BaseQueryHandler[ListAccountsQuery, tuple[tuple[AuthDTO, ...], int]]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, query: ListAccountsQuery) -> tuple[tuple[AuthDTO, ...], int]:
        accounts_iter, total_count = await self._account_repo.list_accounts(limit=query.limit, offset=query.offset)
        accounts = [AuthDTO.from_domain(account) for account in accounts_iter]
        return tuple(accounts), total_count
