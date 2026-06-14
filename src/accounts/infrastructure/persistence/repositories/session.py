from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.domain.session.repositories.session_repository import BaseSessionRepository
from src.accounts.domain.session.session import Session
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.infrastructure.persistence.mappers.session_mapper import SessionMapper
from src.accounts.infrastructure.persistence.tables import SessionTable
from src.shared.infrastructure.database.repository import SQLBaseRepository
from src.shared.infrastructure.persistence.exceptions import RecordNotFoundError


class SQLBaseSessionRepository(SQLBaseRepository[SessionTable], BaseSessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self) -> None:
        super().__init__(SessionTable)

    async def add(self, session: Session) -> None:
        record = SessionMapper.to_record(session)
        self.session.add(record)
        await self.session.flush()

    async def update(self, session: Session) -> None:
        stmt = select(SessionTable).filter(SessionTable.id == session.id.value)
        result = await self.session.execute(stmt)
        record = result.scalars().one_or_none()

        if not record:
            raise RecordNotFoundError(identifier=str(session.id.value))

        SessionMapper.update_record(session, record)
        await self.session.flush()

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        stmt = (
            select(SessionTable)
            .options(
                joinedload(SessionTable.account)
            )  # we Use joinload because the async session does not support lazy loading
            .filter(SessionTable.id == session_id.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().one_or_none()
        if not record:
            raise RecordNotFoundError(identifier=str(session_id.value))
        return SessionMapper.to_domain(record)

    async def get_by_refresh_token(self, token: RefreshToken) -> Session | None:
        stmt = (
            select(SessionTable)
            .options(joinedload(SessionTable.account))
            .filter(SessionTable.refresh_token == token.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().one_or_none()
        return SessionMapper.to_domain(record) if record else None

    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        stmt = (
            select(SessionTable)
            .options(joinedload(SessionTable.account))
            .filter(SessionTable.account_id == account_id.value)
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [SessionMapper.to_domain(record) for record in records]

    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        stmt = (
            update(SessionTable)
            .where(SessionTable.account_id == account_id.value)
            .where(SessionTable.is_active.is_(True))
            .values(is_active=False, is_revoked=True)
        )
        await self.session.execute(stmt)
