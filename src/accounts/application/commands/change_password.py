import uuid

from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...application.dtos.account import AuthDTO
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.hashed_password import HashedPassword
from ...domain.interfaces.account_repository import BaseAccountRepository
from ...domain.interfaces.session_repository import BaseSessionRepository
from ..interfaces.password_hasher import BasePasswordHasher


class ChangePasswordCommand(BaseCommand[AuthDTO], BaseModel):
    account_id: str
    new_password: str


class ChangePasswordHandler(BaseCommandHandler[ChangePasswordCommand, AuthDTO]):
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        password_hasher: BasePasswordHasher,
    ):
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._password_hasher = password_hasher

    async def handle(self, command: ChangePasswordCommand) -> AuthDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(command.account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        hashed = HashedPassword.create(self._password_hasher.encode(command.new_password))
        account.change_password(hashed)

        # Security Side Effect: Revoke all sessions on password change
        await self._session_repo.revoke_all_for_account(account.id)

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)
