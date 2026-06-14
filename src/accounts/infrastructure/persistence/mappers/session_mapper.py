from src.accounts.domain.session.session import Session
from src.accounts.domain.session.value_objects.account_id import AccountId
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken
from src.accounts.domain.session.value_objects.session_id import SessionId
from src.accounts.domain.session.value_objects.session_status import SessionStatus
from src.accounts.infrastructure.persistence.tables import SessionTable


class SessionMapper:
    @staticmethod
    def to_domain(record: SessionTable) -> Session:
        return Session.from_data(
            id=SessionId.create(record.id),
            account_id=AccountId.create(record.account_id),
            refresh_token=RefreshToken.create(record.refresh_token),
            expires_at=record.expires_at,
            status=SessionStatus.create(is_active=record.is_active),
            is_revoked=record.is_revoked,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(session: Session) -> SessionTable:
        return SessionTable(
            id=session.id.value,
            account_id=session.account_id.value,
            refresh_token=session.refresh_token.value,
            expires_at=session.expires_at,
            is_active=session.is_active,
            is_revoked=session.is_revoked,
        )

    @staticmethod
    def update_record(session: Session, record: SessionTable) -> None:
        record.refresh_token = session.refresh_token.value
        record.expires_at = session.expires_at
        record.is_active = session.is_active
        record.is_revoked = session.is_revoked
