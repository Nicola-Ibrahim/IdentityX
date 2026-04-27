import uuid
from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.interfaces.session_repository import SessionRepository
from .....accounts.domain.session.session import Session as DomainSession
from .....accounts.domain.session.value_objects.refresh_token import RefreshToken
from .....accounts.domain.session.value_objects.session_id import SessionId
from .....accounts.domain.session.value_objects.session_status import SessionStatus
from ..orm.models import AccountModel, SessionModel


class SQLSessionRepository(SessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, record: SessionModel) -> DomainSession:
        account_uuid = record.account.uuid  # type: ignore[union-attr]
        account_id = AccountId(uuid.UUID(account_uuid))
        session_id = SessionId(uuid.UUID(record.session_uuid))
        refresh = RefreshToken.create(record.refresh_token)
        status = SessionStatus(is_active=record.is_active)
        session = DomainSession(
            _id=session_id,
            _account_id=account_id,
            _refresh_token=refresh,
            _expires_at=record.expires_at,
            _status=status,
        )
        session._created_at = record.created_at  # type: ignore[attr-defined]
        session._updated_at = record.updated_at  # type: ignore[attr-defined]
        return session

    def add(self, session_domain: DomainSession) -> None:
        with self._session_factory() as session:  # type: Session
            account_record = (
                session.query(AccountModel).filter(AccountModel.uuid == str(session_domain.account_id.value)).one()
            )
            record = SessionModel(
                session_uuid=str(session_domain.id.value),
                account_id=account_record.id,
                refresh_token=session_domain.refresh_token.value,
                expires_at=session_domain.expires_at,
                is_active=session_domain.is_active,
            )
            session.add(record)
            session.commit()

    def update(self, session_domain: DomainSession) -> None:
        with self._session_factory() as session:  # type: Session
            record = (
                session.query(SessionModel)
                .filter(SessionModel.session_uuid == str(session_domain.id.value))
                .one_or_none()
            )
            if not record:
                raise ValueError("Session not found")
            record.refresh_token = session_domain.refresh_token.value
            record.expires_at = session_domain.expires_at
            record.is_active = session_domain.is_active
            session.commit()

    def get_by_id(self, session_id: SessionId) -> Optional[DomainSession]:
        with self._session_factory() as session:  # type: Session
            record = (
                session.query(SessionModel)
                .join(SessionModel.account)
                .filter(SessionModel.session_uuid == str(session_id.value))
                .one_or_none()
            )
            return self._to_domain(record) if record else None

    def list_for_account(self, account_id: AccountId) -> Iterable[DomainSession]:
        with self._session_factory() as session:  # type: Session
            records = (
                session.query(SessionModel)
                .join(SessionModel.account)
                .filter(AccountModel.uuid == str(account_id.value))
                .all()
            )
            return [self._to_domain(record) for record in records]

    def revoke_all_for_account(self, account_id: AccountId) -> None:
        with self._session_factory() as session:  # type: Session
            records = (
                session.query(SessionModel)
                .join(SessionModel.account)
                .filter(AccountModel.uuid == str(account_id.value), SessionModel.is_active.is_(True))
                .all()
            )
            for record in records:
                record.is_active = False
            session.commit()
