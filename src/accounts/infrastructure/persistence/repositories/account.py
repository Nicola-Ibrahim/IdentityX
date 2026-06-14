from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.accounts.domain.account.account import Account
from src.accounts.domain.account.repositories.account_repository import BaseAccountRepository
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.infrastructure.persistence.mappers.account_mapper import AccountMapper
from src.accounts.infrastructure.persistence.tables import AccountTable, ExternalIdentityTable
from src.shared.infrastructure.database.repository import SQLBaseRepository
from src.shared.infrastructure.persistence.exceptions import RecordConflictError, RecordNotFoundError


class SQLBaseAccountRepository(SQLBaseRepository[AccountTable], BaseAccountRepository):
    """SQLAlchemy implementation of :class:`BaseAccountRepository`."""

    def __init__(self):
        super().__init__(AccountTable)

    # Interface implementation -------------------------------------------------
    async def add(self, account: Account) -> None:
        record = AccountMapper.to_record(account)
        self.session.add(record)

        try:
            # Flush is asynchronous and catches the DB constraints
            await self.session.flush()
        except IntegrityError:
            raise RecordConflictError(identifier=str(account.email))

    async def update(self, account: Account) -> None:
        result = await self.session.execute(
            select(AccountTable)
            .options(selectinload(AccountTable.external_identities), selectinload(AccountTable.trusted_devices))
            .filter(AccountTable.id == account.id.value)
        )
        record = result.scalars().first()
        if not record:
            raise RecordNotFoundError(identifier=str(account.id.value))

        AccountMapper.update_record(account, record)
        await self.session.flush()

    async def get_by_id(self, account_id: AccountId) -> Account | None:
        stmt = (
            select(AccountTable)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(AccountTable.id == account_id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if not record:
            raise RecordNotFoundError(identifier=str(account_id.value))
        return AccountMapper.to_domain(record)

    async def get_by_email(self, email: str) -> Account | None:
        stmt = (
            select(AccountTable)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(AccountTable.email == email)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return AccountMapper.to_domain(record) if record else None

    async def get_by_external_identity(self, provider: str, provider_user_id: str) -> Account | None:
        stmt = (
            select(AccountTable)
            .join(AccountTable.external_identities)
            .options(
                selectinload(AccountTable.sessions),
                selectinload(AccountTable.external_identities),
                selectinload(AccountTable.trusted_devices),
            )
            .filter(ExternalIdentityTable.provider == provider.lower())
            .filter(ExternalIdentityTable.provider_user_id == provider_user_id)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        return AccountMapper.to_domain(record) if record else None

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(AccountTable.id).filter(AccountTable.email == email)
        result = await self.session.execute(stmt)
        return result.first() is not None

    async def list_accounts(self, limit: int = 100, offset: int = 0) -> Iterable[any]:
        stmt = (
            select(AccountTable)
            .options(selectinload(AccountTable.external_identities), selectinload(AccountTable.trusted_devices))
            .order_by(AccountTable.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def remove(self, account_id: AccountId) -> None:
        stmt = select(AccountTable).filter(AccountTable.id == account_id.value)
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record:
            await self.session.delete(record)
