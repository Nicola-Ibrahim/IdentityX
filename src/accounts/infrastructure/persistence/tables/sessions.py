import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.table import BaseSQLTable


class SessionTable(BaseSQLTable):
    """
    SQLAlchemy model for the 'sessions' table.
    Tracks active user sessions and refresh tokens.
    """

    __tablename__ = "sessions"

    __table_args__ = (
        Index("idx_session_account_active", "account_id", "is_active"),
        Index("idx_session_refresh_token", "refresh_token", unique=True),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    account: Mapped["AccountTable"] = relationship("AccountTable", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, active={self.is_active})>"
