import uuid

from pydantic import BaseModel

from building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from accounts.domain.account.value_objects.account_id import AccountId
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from accounts.application.dtos.account import AccountDTO


class GetAccountByIdQuery(BaseModel, BaseQuery[AccountDTO | None]):
    account_id: str


class GetAccountByIdHandler(BaseQueryHandler[GetAccountByIdQuery, AccountDTO | None]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, query: GetAccountByIdQuery) -> AccountDTO | None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(query.account_id))
        except (ValueError, AttributeError):
            return None

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            return None
        return AccountDTO.from_domain(account)
