from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ......database.models import BaseSQLModel


class AccountORM(BaseSQLModel):
    """
    SQLAlchemy model for the 'accounts' table.
    Maps directly to the Account Aggregate Root.
    """

    __tablename__ = "accounts"

    # Identity
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Credentials
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)

    # Status (Flattened from AccountStatus value object)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Permissions
    roles: Mapped[str] = mapped_column(String(256), nullable=False, default="user")

    # Audit fields are inherited from BaseSQLModel (id, created_at, updated_at)

    # Relationships
    sessions: Mapped[List["SessionORM"]] = relationship(
        "SessionORM", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account(uuid={self.uuid}, email={self.email}, active={self.is_active})>"
