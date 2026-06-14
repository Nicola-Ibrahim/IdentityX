from typing import override
from pydantic import BaseModel

from src.accounts.application.account.dtos.account import AccountDTO
from src.accounts.application.account.queries.list_accounts_query_service import ListAccountsQueryService
from src.shared.building_blocks.application.mediator import BaseQuery, BaseQueryHandler


class ListAccountsQuery(BaseModel, BaseQuery[tuple[AccountDTO, ...]]):
    limit: int = 100
    offset: int = 0


class ListAccountsHandler(BaseQueryHandler[ListAccountsQuery, tuple[AccountDTO, ...]]):
    def __init__(self, query_service: ListAccountsQueryService):
        self._query_service = query_service

    @override
    async def handle(self, query: ListAccountsQuery) -> tuple[AccountDTO, ...]:
        return await self._query_service.list_accounts(limit=query.limit, offset=query.offset)
