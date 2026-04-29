import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from .....accounts.domain.account.value_objects.account_id import AccountId
from .....accounts.domain.interfaces.session_repository import SessionRepository
from .....accounts.domain.session.session import Session
from .....accounts.domain.session.value_objects.refresh_token import RefreshToken
from .....accounts.domain.session.value_objects.session_id import SessionId
from .....accounts.domain.session.value_objects.session_status import SessionStatus
from ..orm.models import AccountModel, SessionModel


class SQLSessionRepository(SessionRepository):
    """SQLAlchemy repository for session aggregates."""

    def __init__(self, session: Session) -> None:
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

    def add(self, session_domain: Session) -> None:
        account_record = (
            self._session.query(AccountModel).filter(AccountModel.uuid == str(session_domain.account_id.value)).one()
        )
        record = SessionModel(
            session_uuid=str(session_domain.id.value),
            account_id=account_record.id,
            refresh_token=session_domain.refresh_token.value,
            expires_at=session_domain.expires_at,
            is_active=session_domain.is_active,
        )
        self._session.add(record)

    def update(self, session_domain: DomainSession) -> None:
        record = (
            self._session.query(SessionModel)
            .filter(SessionModel.session_uuid == str(session_domain.id.value))
            .one_or_none()
        )
        if not record:
            raise ValueError("Session not found")
        record.refresh_token = session_domain.refresh_token.value
        record.expires_at = session_domain.expires_at
        record.is_active = session_domain.is_active

    def get_by_id(self, session_id: SessionId) -> Optional[Session]:
        record = (
            self._session.query(SessionModel)
            .join(SessionModel.account)
            .filter(SessionModel.session_uuid == str(session_id.value))
            .one_or_none()
        )
        return self._to_domain(record) if record else None

    def get_by_refresh_token(self, token: RefreshToken) -> Optional[Session]:
        record = (
            self._session.query(SessionModel)
            .join(SessionModel.account)
            .filter(SessionModel.refresh_token == token.value)
            .one_or_none()
        )
        return self._to_domain(record) if record else None

    def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        records = (
            self._session.query(SessionModel)
            .join(SessionModel.account)
            .filter(AccountModel.uuid == str(account_id.value))
            .all()
        )
        return [self._to_domain(record) for record in records]

    def revoke_all_for_account(self, account_id: AccountId) -> None:
        records = self._session.query(SessionModel).filter(
            SessionModel.account_id.in_(
                self._session.query(AccountModel.id).filter(AccountModel.uuid == str(account_id.value))
            ),
            SessionModel.is_active.is_(True),
        )
        records.update({"is_active": False}, synchronize_session=False)
