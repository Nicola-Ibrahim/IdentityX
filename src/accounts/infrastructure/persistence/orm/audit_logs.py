from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .....buckets.database.table import BaseSQLTable


class AuditLogTable(BaseSQLTable):
    """
    SQLAlchemy model for the 'audit_logs' table.
    """

    __tablename__ = "audit_logs"

    account_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(512), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, account_id={self.account_id})>"
