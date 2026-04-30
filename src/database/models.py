from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class BaseSQLModel(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in IdentityX.
    Provides standard identity and audit fields.
    """
    
    # Primary Key - using integer for internal DB efficiency
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
