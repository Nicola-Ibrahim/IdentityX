from typing import override
from pydantic import BaseModel

from accounts.application.dtos.account import AccountDTO
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from building_blocks.application.mediator import BaseQuery, BaseQueryHandler


class ListAccountsQuery(BaseModel, BaseQuery[tuple[AccountDTO, ...]]):
    limit: int = 100
    offset: int = 0


class ListAccountsHandler(BaseQueryHandler[ListAccountsQuery, tuple[AccountDTO, ...]]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    @override
    async def handle(self, query: ListAccountsQuery) -> tuple[AccountDTO, ...]:
        records = await self._account_repo.list_accounts(limit=query.limit, offset=query.offset)
        accounts = [
            AccountDTO(
                id=str(record.id),
                email=record.email,
                is_verified=record.is_verified,
                is_active=record.is_active,
                roles=tuple(r.role for r in record.roles) if hasattr(record, "roles") else (),
            )
            for record in records
        ]
        return tuple(accounts)
