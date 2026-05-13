from pydantic import BaseModel

from ....building_blocks.application.mediator import BaseCommand, BaseCommandHandler
from ...domain.account.account import Account
from ...domain.account.value_objects.email import Email
from ...domain.account.value_objects.hashed_password import HashedPassword
from ...domain.account.value_objects.password import Password
from ...domain.interfaces.account_repository import BaseAccountRepository
from ..dtos.account import AuthDTO
from ..interfaces.notification_service import BaseNotificationService
from ..interfaces.password_hasher import BasePasswordHasher


class RegisterAccountCommand(BaseCommand[AuthDTO], BaseModel):
    email: str
    password: str


class RegisterAccountHandler(BaseCommandHandler[RegisterAccountCommand, AuthDTO]):
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        notification_service: BaseNotificationService,
        password_hasher: BasePasswordHasher,
    ):
        self._account_repo = account_repo
        self._notification_service = notification_service
        self._password_hasher = password_hasher

    async def handle(self, command: RegisterAccountCommand) -> AuthDTO:
        email_vo = Email.create(command.email)
        password_vo = Password.create(command.password)
        hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))
        account = Account.register(email=email_vo, password=hashed)
        await self._account_repo.add(account)
        await self._notification_service.send_welcome_email(str(email_vo))
        return AuthDTO.from_domain(account)
