from typing import override
from pydantic import BaseModel

from accounts.application.dtos.account import AccountDTO
from accounts.application.interfaces.notification_service import BaseNotificationService
from accounts.application.interfaces.password_hasher import BasePasswordHasher
from accounts.domain.account.account import Account
from accounts.domain.account.value_objects.email import Email
from accounts.domain.account.value_objects.hashed_password import HashedPassword
from accounts.domain.account.value_objects.password import Password
from accounts.domain.interfaces.account_repository import BaseAccountRepository
from building_blocks.application.mediator import BaseCommand, BaseCommandHandler


class RegisterAccountCommand(BaseModel, BaseCommand[AccountDTO]):
    email: str
    password: str


class RegisterAccountHandler(BaseCommandHandler[RegisterAccountCommand, AccountDTO]):
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        notification_service: BaseNotificationService,
        password_hasher: BasePasswordHasher,
    ):
        self._account_repo = account_repo
        self._notification_service = notification_service
        self._password_hasher = password_hasher

    @override
    async def handle(self, command: RegisterAccountCommand) -> AccountDTO:
        email_vo = Email.create(command.email)
        password_vo = Password.create(command.password)
        hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))
        account = Account.register(email=email_vo, password=hashed)
        await self._account_repo.add(account)
        await self._notification_service.send_welcome_email(str(email_vo))
        return AccountDTO(
            id=str(account.id.value),
            email=str(account.email),
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=tuple(r.value for r in account.roles),
        )
