from typing import Iterable

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .....accounts.domain.interfaces.session_repository import BaseSessionRepository
from .....accounts.domain.session.session import Session
from .....accounts.domain.session.value_objects.account_id import AccountId
from .....accounts.domain.session.value_objects.refresh_token import RefreshToken
from .....accounts.domain.session.value_objects.session_id import SessionId
from .....accounts.domain.session.value_objects.session_status import SessionStatus
from ..exceptions import SessionRecordNotFoundError
from ..orm.models import SessionORM


class SQLBaseSessionRepository(BaseSessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    def _to_domain(self, record: SessionORM) -> Session:
        account_id = AccountId.create(record.account.id)
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

    async def add(self, session_domain: Session) -> None:
        record = SessionORM(
            id=session_domain.id.value,
            account_id=session_domain.account_id.value,
            refresh_token=session_domain.refresh_token.value,
            expires_at=session_domain.expires_at,
            is_active=session_domain.is_active,
            is_revoked=session_domain.is_revoked,
        )
        self._db_session.add(record)

    async def update(self, session_domain: Session) -> None:
        stmt = select(SessionORM).filter(SessionORM.id == session_domain.id.value)
        result = await self._db_session.execute(stmt)
        record = result.scalars().one_or_none()
        if not record:
            raise SessionRecordNotFoundError(str(session_domain.id.value))
        record.refresh_token = session_domain.refresh_token.value
        record.expires_at = session_domain.expires_at
        record.is_active = session_domain.is_active
        record.is_revoked = session_domain.is_revoked

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        stmt = select(SessionORM).options(joinedload(SessionORM.account)).filter(SessionORM.id == session_id.value)
        result = await self._db_session.execute(stmt)
        record = result.scalars().one_or_none()
        return self._to_domain(record) if record else None

    async def get_by_refresh_token(self, token: RefreshToken) -> Session | None:
        stmt = (
            select(SessionORM).options(joinedload(SessionORM.account)).filter(SessionORM.refresh_token == token.value)
        )
        result = await self._db_session.execute(stmt)
        record = result.scalars().one_or_none()
        return self._to_domain(record) if record else None

    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        stmt = (
            select(SessionORM)
            .options(joinedload(SessionORM.account))
            .filter(SessionORM.account_id == account_id.value)
        )
        result = await self._db_session.execute(stmt)
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        stmt = (
            update(SessionORM)
            .where(SessionORM.account_id == account_id.value)
            .where(SessionORM.is_active.is_(True))
            .values(is_active=False, is_revoked=True)
        )
        await self._session.execute(stmt)
