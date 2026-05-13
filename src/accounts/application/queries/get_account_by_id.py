import uuid

from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseQuery, BaseQueryHandler
from ...domain.account.value_objects.account_id import AccountId
from ...domain.interfaces.account_repository import BaseAccountRepository
from ..dtos.account import AuthDTO


class GetAccountByIdQuery(BaseQuery[AuthDTO | None], BaseModel):
    account_id: str


class GetAccountByIdHandler(BaseQueryHandler[GetAccountByIdQuery, AuthDTO | None]):
    def __init__(self, account_repo: BaseAccountRepository):
        self._account_repo = account_repo

    async def handle(self, query: GetAccountByIdQuery) -> AuthDTO | None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(query.account_id))
        except (ValueError, AttributeError):
            return None

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            return None
        return AuthDTO.from_domain(account)
