import uuid

from .....building_blocks.domain.result import Result
from ....domain.account.account import Account
from ....domain.account.value_objects.account_id import AccountId
from ....domain.account.value_objects.email import Email
from ....domain.account.value_objects.hashed_password import HashedPassword
from ....domain.account.value_objects.password import Password
from ....domain.interfaces.account_repository import BaseAccountRepository
from ....domain.interfaces.session_repository import BaseSessionRepository
from ...interfaces.notification_service import BaseNotificationService
from ...interfaces.password_hasher import BasePasswordHasher
from .dtos.account import AuthDTO

class AccountService:
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        password_hasher: BasePasswordHasher,
        notification_service: BaseNotificationService,
    ) -> None:
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._password_hasher = password_hasher
        self._notifications = notification_service

    @Result.capture
    async def register(self, email: str, password: str) -> tuple[Account, AuthDTO]:
        email_vo = Email.create(email)
        password_vo = Password.create(password)

        hashed = HashedPassword.create(self._password_hasher.encode(password_vo.value))

        account = Account.register(email=email_vo, password=hashed)

        await self._account_repo.add(account)

        await self._notifications.send_welcome_email(str(email_vo))

        return AuthDTO.from_domain(account)

    @Result.capture
    async def get_by_id(self, account_id: str) -> AuthDTO:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError):
            return None

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            return None
        return AuthDTO.from_domain(account)

    @Result.capture
    async def list(self, limit: int = 100, offset: int = 0) -> tuple[tuple[AuthDTO, ...], int]:
        accounts_iter, total_count = await self._account_repo.list_accounts(limit=limit, offset=offset)
        accounts = [AuthDTO.from_domain(account) for account in accounts_iter]
        return tuple(accounts), total_count

    @Result.capture
    async def change_email(self, account_id: str, new_email: str) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.change_email(Email.create(new_email))

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def change_password(self, account_id: str, new_password: str) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        hashed = HashedPassword.create(self._password_hasher.encode(new_password))
        account.change_password(hashed)

        # Security Side Effect: Revoke all sessions on password change
        await self._session_repo.revoke_all_for_account(account.id)

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def set_activation_status(self, account_id: str, is_active: bool) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))

        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if is_active:
            account.activate()
        else:
            account.deactivate()
            # Security Side Effect: Revoke all sessions on deactivation
            await self._session_repo.revoke_all_for_account(account.id)

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def remove(self, account_id: str) -> None:
        try:
            account_id_vo = AccountId.create(uuid.UUID(account_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid account identifier") from exc

        await self._account_repo.remove(account_id_vo)

    @Result.capture
    async def verify(self, account_id: str) -> tuple[Account, AuthDTO]:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.verify()
        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def deactivate(self, account_id: str) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.deactivate()
        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def activate(self, account_id: str) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        account.activate()
        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)

    @Result.capture
    async def update(self, account_id: str, data: dict) -> AuthDTO:
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        account = await self._account_repo.get_by_id(account_id_vo)
        if not account:
            raise ValueError("Account not found")

        if "email" in data:
            account.change_email(Email.create(data["email"]))

        await self._account_repo.update(account)
        return AuthDTO.from_domain(account)
