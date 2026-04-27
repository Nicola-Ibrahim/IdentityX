from datetime import datetime, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from ....domain.interfaces.token_denylist_repository import TokenDenylistRepository
from ..orm.models import RevokedTokenModel


class SQLTokenDenylistRepository(TokenDenylistRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add(self, jti: str, expires_at: datetime) -> None:
        with self._session_factory() as session:
            # Ensure expires_at is timezone-aware if not already
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            token = RevokedTokenModel(jti=jti, expires_at=expires_at)
            session.add(token)
            session.commit()

    def is_revoked(self, jti: str) -> bool:
        with self._session_factory() as session:
            stmt = select(RevokedTokenModel).where(RevokedTokenModel.jti == jti)
            result = session.execute(stmt).scalar_one_or_none()
            return result is not None

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        with self._session_factory() as session:
            stmt = delete(RevokedTokenModel).where(RevokedTokenModel.expires_at < now)
            result = session.execute(stmt)
            count = result.rowcount
            session.commit()
            return count
