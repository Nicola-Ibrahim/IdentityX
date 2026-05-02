import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseSQLTable(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in IdentityX.
    Provides standard identity and audit fields.
    """

    # Primary Key - using UUID for security and distributed generation
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
