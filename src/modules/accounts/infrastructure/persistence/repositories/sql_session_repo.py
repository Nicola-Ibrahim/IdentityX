import uuid
from typing import Iterable, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.interfaces.session_repository import SessionRepository
from .....accounts.domain.session.session import Session
from .....accounts.domain.session.value_objects.refresh_token import RefreshToken
from .....accounts.domain.session.value_objects.session_id import SessionId
from .....accounts.domain.session.value_objects.session_status import SessionStatus
from ..orm.models import AccountModel, SessionModel


class SQLSessionRepository(SessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, record: SessionModel) -> Session:
        account_uuid = record.account.uuid
        account_id = AccountId(uuid.UUID(account_uuid))
        session_id = SessionId(uuid.UUID(record.session_uuid))
        refresh = RefreshToken.create(record.refresh_token)
        status = SessionStatus(is_active=record.is_active)
        session = Session(
            _id=session_id,
            _account_id=account_id,
            _refresh_token=refresh,
            _expires_at=record.expires_at,
            _status=status,
        )
        session._created_at = record.created_at
        session._updated_at = record.updated_at
        return session

    async def add(self, session_domain: Session) -> None:
        result = await self._session.execute(
            select(AccountModel).filter(AccountModel.uuid == str(session_domain.account_id.value))
        )
        account_record = result.scalars().one()
        record = SessionModel(
            session_uuid=str(session_domain.id.value),
            account_id=account_record.id,
            refresh_token=session_domain.refresh_token.value,
            expires_at=session_domain.expires_at,
            is_active=session_domain.is_active,
        )
        self._session.add(record)

    async def update(self, session_domain: Session) -> None:
        result = await self._session.execute(
            select(SessionModel).filter(SessionModel.session_uuid == str(session_domain.id.value))
        )
        record = result.scalars().one_or_none()
        if not record:
            raise ValueError("Session not found")
        record.refresh_token = session_domain.refresh_token.value
        record.expires_at = session_domain.expires_at
        record.is_active = session_domain.is_active

    async def get_by_id(self, session_id: SessionId) -> Optional[Session]:
        result = await self._session.execute(
            select(SessionModel)
            .join(SessionModel.account)
            .filter(SessionModel.session_uuid == str(session_id.value))
        )
        record = result.scalars().one_or_none()
        return self._to_domain(record) if record else None

    async def get_by_refresh_token(self, token: RefreshToken) -> Optional[Session]:
        result = await self._session.execute(
            select(SessionModel)
            .join(SessionModel.account)
            .filter(SessionModel.refresh_token == token.value)
        )
        record = result.scalars().one_or_none()
        return self._to_domain(record) if record else None

    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        result = await self._session.execute(
            select(SessionModel)
            .join(SessionModel.account)
            .filter(AccountModel.uuid == str(account_id.value))
        )
        records = result.scalars().all()
        return [self._to_domain(record) for record in records]

    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        # We need the account.id (integer) to filter sessions
        account_id_subquery = select(AccountModel.id).filter(AccountModel.uuid == str(account_id.value))
        
        stmt = (
            update(SessionModel)
            .where(SessionModel.account_id.in_(account_id_subquery))
            .where(SessionModel.is_active.is_(True))
            .values(is_active=False)
        )
        await self._session.execute(stmt)
