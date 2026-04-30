from typing import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .....accounts.domain.account.account import Account
from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.account.value_objects.account_role import AccountRole
from .....accounts.domain.account.value_objects.account_status import AccountStatus
from .....accounts.domain.account.value_objects.email import Email
from .....accounts.domain.account.value_objects.hashed_password import HashedPassword
from .....accounts.domain.account.value_objects.session_id import SessionId
from .....accounts.domain.interfaces.account_repository import BaseAccountRepository
from ..exceptions import AccountRecordConflictError, AccountRecordNotFoundError
from ..orm.models import AccountORM


class SQLBaseAccountRepository(BaseAccountRepository):
    """SQLAlchemy implementation of :class:`BaseAccountRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, record: AccountORM) -> Account:
        id = AccountId.create(record.id)
        email = Email.create(record.email)
        password = HashedPassword.create(record.hashed_password)
        status = AccountStatus.create(is_verified=record.is_verified, is_active=record.is_active)
        roles = {AccountRole(r.strip()) for r in record.roles.split(",") if r.strip()}

        # Extract session IDs if available
        session_ids = []
        try:
            session_ids = [SessionId.create(s.id) for s in record.sessions]
        except Exception:
            # If not loaded, we leave it empty to avoid accidental lazy-loading errors
            pass

        return Account.from_data(
            id=id,
            email=email,
            password=password,
            status=status,
            roles=roles,
            created_at=record.created_at,
            updated_at=record.updated_at,
            session_ids=session_ids,
        )

    # Interface implementation -------------------------------------------------
    async def add(self, account: Account) -> None:
        record = AccountORM(
            id=account.id.value,
            email=str(account.email),
            hashed_password=account.hashed_password.value,
            is_verified=account.is_verified,
            is_active=account.is_active,
            roles=",".join(r.value for r in account.roles),
        )
        self._session.add(record)
        try:
            await self._session.flush()
        except IntegrityError:
            raise AccountRecordConflictError(str(account.email))

    async def update(self, account: Account) -> None:
        result = await self._session.execute(select(AccountORM).filter(AccountORM.id == account.id.value))
        db_account = result.scalars().first()
        if not db_account:
            raise AccountRecordNotFoundError(str(account.id.value))

        db_account.email = str(account.email)
        db_account.hashed_password = account.hashed_password.value
        db_account.is_active = account.is_active
        db_account.is_verified = account.is_verified
        db_account.roles = ",".join(r.value for r in account.roles)

    async def get_by_id(self, account_id: AccountId) -> Account | None:
        stmt = select(AccountORM).options(selectinload(AccountORM.sessions)).filter(AccountORM.id == account_id.value)
        result = await self._session.execute(stmt)
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def get_by_email(self, email: str) -> Account | None:
        stmt = select(AccountORM).options(selectinload(AccountORM.sessions)).filter(AccountORM.email == email)
        result = await self._session.execute(stmt)
        record = result.scalars().first()
        return self._to_domain(record) if record else None

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(AccountORM.id).filter(AccountORM.email == email)
        result = await self._session.execute(stmt)
        return result.first() is not None

    async def list_accounts(self) -> Iterable[Account]:
        stmt = select(AccountORM).order_by(AccountORM.created_at.asc())
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    async def remove(self, account_id: AccountId) -> None:
        stmt = select(AccountORM).filter(AccountORM.id == account_id.value)
        result = await self._session.execute(stmt)
        record = result.scalars().first()
        if record:
            await self._session.delete(record)
