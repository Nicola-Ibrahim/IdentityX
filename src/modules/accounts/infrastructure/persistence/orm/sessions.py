from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ......database.models import BaseSQLModel


class SessionORM(BaseSQLModel):
    """
    SQLAlchemy model for the 'sessions' table.
    Tracks active user sessions and refresh tokens.
    """

    __tablename__ = "sessions"

    session_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    account: Mapped["AccountORM"] = relationship("AccountORM", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(uuid={self.session_uuid}, active={self.is_active})>"
