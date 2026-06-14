from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.table import BaseSQLTable


class AccountTable(BaseSQLTable):
    """
    SQLAlchemy model for the 'accounts' table.
    Maps directly to the Account Aggregate Root.
    """

    __tablename__ = "accounts"

    # Credentials
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Status (Flattened from AccountStatus value object)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Permissions
    roles: Mapped[str] = mapped_column(String(256), nullable=False, default="user")

    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(256), nullable=True)
    mfa_recovery_codes: Mapped[str | None] = mapped_column(String, nullable=True)  # comma-separated hashed codes

    # Audit fields are inherited from BaseSQLTable (id, created_at, updated_at)

    # Relationships
    sessions: Mapped[list["SessionTable"]] = relationship(
        "SessionTable", back_populates="account", cascade="all, delete-orphan"
    )
    external_identities: Mapped[list["ExternalIdentityTable"]] = relationship(
        "ExternalIdentityTable", back_populates="account", cascade="all, delete-orphan"
    )
    trusted_devices: Mapped[list["TrustedDeviceTable"]] = relationship(
        "TrustedDeviceTable", back_populates="account", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, email={self.email}, active={self.is_active})>"
