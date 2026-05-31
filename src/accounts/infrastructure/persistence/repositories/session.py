from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from src.buckets.database.repository import SQLBaseRepository
from src.building_blocks.infrastructure.persistance.exceptions import RecordNotFoundError
from src.building_blocks.application.mediator import Mediator

from src.accounts.domain.interfaces.session_repository import BaseSessionRepository
from src.accounts.domain.session.session import Session
from src.accounts.domain.session.value_objects.account_id import AccountId
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.domain.session.value_objects.session_status import SessionStatus
from src.accounts.infrastructure.persistence.orm.models import SessionTable


class SQLBaseSessionRepository(SQLBaseRepository[SessionTable], BaseSessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self, mediator: Mediator | None = None) -> None:
        self._mediator = mediator
        super().__init__(SessionTable)

    def _to_domain(self, record: SessionTable) -> Session:
        account_id = AccountId.create(record.account_id)
        session_id = SessionId.create(record.id)
        refresh = RefreshToken.create(record.refresh_token)
        status = SessionStatus.create(is_active=record.is_active)

        return Session.from_data(
            id=session_id,
            account_id=account_id,
            refresh_token=refresh,
            expires_at=record.expires_at,
            status=status,
            is_revoked=record.is_revoked,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    async def add(self, session: Session) -> None:
        record = SessionTable(
            id=session.id.value,
            account_id=session.account_id.value,
            refresh_token=session.refresh_token.value,
            expires_at=session.expires_at,
            is_active=session.is_active,
            is_revoked=session.is_revoked,
        )
        self.session.add(record)
        await self.session.flush()

        if self._mediator:
            for event in session.pull_events():
                await self._mediator.publish(event)

    async def update(self, session: Session) -> None:
        stmt = select(SessionTable).filter(SessionTable.id == session.id.value)
        result = await self.session.execute(stmt)
        record = result.scalars().one_or_none()

        if not record:
            raise RecordNotFoundError(identifier=str(session.id.value))

        record.refresh_token = session.refresh_token.value
        record.expires_at = session.expires_at
        record.is_active = session.is_active
        record.is_revoked = session.is_revoked

        await self.session.flush()

        if self._mediator:
            for event in session.pull_events():
                await self._mediator.publish(event)

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
        return self._to_domain(record)

    async def get_by_refresh_token(self, token: RefreshToken) -> Session | None:
        stmt = (
            select(SessionTable)
            .options(joinedload(SessionTable.account))
            .filter(SessionTable.refresh_token == token.value)
        )
        result = await self.session.execute(stmt)
        record = result.scalars().one_or_none()
        return self._to_domain(record) if record else None

    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        stmt = (
            select(SessionTable)
            .options(joinedload(SessionTable.account))
            .filter(SessionTable.account_id == account_id.value)
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        stmt = (
            update(SessionTable)
            .where(SessionTable.account_id == account_id.value)
            .where(SessionTable.is_active.is_(True))
            .values(is_active=False, is_revoked=True)
        )
        await self.session.execute(stmt)
