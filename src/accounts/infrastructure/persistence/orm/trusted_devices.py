from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .....buckets.database.table import BaseSQLTable

if TYPE_CHECKING:
    from .accounts import AccountTable


class TrustedDeviceTable(BaseSQLTable):
    __tablename__ = "trusted_devices"

    account_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    device_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped["AccountTable"] = relationship("AccountTable", back_populates="trusted_devices")
