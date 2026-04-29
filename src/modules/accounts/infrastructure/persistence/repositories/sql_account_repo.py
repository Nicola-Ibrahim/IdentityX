import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .....accounts.domain.account.account import Account
from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.account.value_objects.account_role import AccountRole
from .....accounts.domain.account.value_objects.account_status import AccountStatus
from .....accounts.domain.account.value_objects.email import Email
from .....accounts.domain.account.value_objects.hashed_password import HashedPassword
from .....accounts.domain.interfaces.account_repository import BaseAccountRepository
from ..orm.models import AccountModel


class SQLBaseAccountRepository(BaseAccountRepository):
    """SQLAlchemy implementation of :class:`BaseAccountRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, record: AccountModel) -> Account:
        id = AccountId.create(uuid.UUID(record.uuid))
        email = Email.create(record.email)
        password = HashedPassword.create(record.hashed_password)
        status = AccountStatus.create(is_verified=record.is_verified, is_active=record.is_active)
        roles = {AccountRole(r.strip()) for r in record.roles.split(",") if r.strip()}
        return Account.from_data(
            id=id,
            email=email,
            password=password,
            status=status,
            roles=roles,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    # Interface implementation -------------------------------------------------
    async def add(self, account: Account) -> None:
        record = AccountModel(
            uuid=str(account.id.value),
            email=str(account.email),
            hashed_password=account.hashed_password.value,
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=",".join(r.value for r in account.roles),
        )
        self._session.add(record)

    async def update(self, account: Account) -> None:
        result = await self._session.execute(select(AccountModel).filter(AccountModel.uuid == str(account.id.value)))
        db_account = result.scalars().first()
        if not db_account:
            raise ValueError("Account not found")

        db_account.email = str(account.email)
        db_account.hashed_password = account.hashed_password.value
        db_account.is_active = account.is_active
        db_account.is_verified = account.is_verified
        db_account.roles = ",".join(r.value for r in account.roles)

    async def get_by_id(self, account_id: AccountId) -> Account | None:
        result = await self._session.execute(select(AccountModel).filter(AccountModel.uuid == str(account_id.value)))
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def get_by_email(self, email: str) -> Account | None:
        result = await self._session.execute(select(AccountModel).filter(AccountModel.email == email))
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def exists_by_email(self, email: str) -> bool:
        result = await self._session.execute(select(AccountModel.uuid).filter(AccountModel.email == email))
        return result.first() is not None

    async def list_accounts(self) -> Iterable[Account]:
        result = await self._session.execute(select(AccountModel).order_by(AccountModel.created_at.asc()))
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    async def remove(self, account_id: AccountId) -> None:
        result = await self._session.execute(select(AccountModel).filter(AccountModel.uuid == str(account_id.value)))
        record = result.scalars().first()
        if record:
            await self._session.delete(record)
