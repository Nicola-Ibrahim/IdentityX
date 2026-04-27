from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship

from ......database.models import BaseSQLModel

# Association table linking accounts and roles.
account_roles = Table(
    "account_roles",
    BaseSQLModel.metadata,
    Column("account_id", ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(BaseSQLModel):
    __tablename__ = "users"

    # Store the domain identifier as a string UUID. This ensures
    # deterministic mapping between the domain aggregate and the
    # persistence layer. The column is unique and non‑null to prevent
    # duplicates and allow efficient lookups.
    uuid = Column(String(36), unique=True, nullable=False, index=True)

    # A unique email address for the user
    email = Column(String(320), unique=True, nullable=False, index=True)
    # The hashed password (e.g. SHA256, bcrypt etc.)
    hashed_password = Column(String(256), nullable=False)
    # Whether the user has completed email verification
    is_verified = Column(Boolean, nullable=False, default=False)
    # Whether the user account is active
    is_active = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<User(id={self.id}, uuid={self.uuid}, email={self.email}, "
            f"verified={self.is_verified}, active={self.is_active})>"
        )


class AccountModel(BaseSQLModel):  # type: ignore[misc]
    __tablename__ = "accounts"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    credential = relationship(
        "CredentialModel",
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sessions = relationship("SessionModel", back_populates="account", cascade="all, delete-orphan")
    roles = relationship("RoleModel", secondary=account_roles, back_populates="accounts")


class CredentialModel(BaseSQLModel):  # type: ignore[misc]
    __tablename__ = "account_credentials"

    account_id = Column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    hashed_password = Column(String(512), nullable=False)

    account = relationship("AccountModel", back_populates="credential")


class SessionModel(BaseSQLModel):  # type: ignore[misc]
    __tablename__ = "sessions"

    session_uuid = Column(String(36), unique=True, nullable=False, index=True)
    account_id = Column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token = Column(String(512), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    account = relationship("AccountModel", back_populates="sessions")


class RoleModel(BaseSQLModel):  # type: ignore[misc]
    __tablename__ = "roles"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    accounts = relationship("AccountModel", secondary=account_roles, back_populates="roles")


class RevokedTokenModel(BaseSQLModel):
    """Stores JTI of revoked tokens until they expire naturally."""
    __tablename__ = "revoked_tokens"

    jti = Column(String(36), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
