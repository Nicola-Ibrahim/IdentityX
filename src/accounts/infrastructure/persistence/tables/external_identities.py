from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infrastructure.database.table import BaseSQLTable
class ExternalIdentityTable(BaseSQLTable):
    """
    SQLAlchemy model for the 'external_identities' table.
    Links an account to an external provider (OAuth2/OIDC).
    """

    __tablename__ = "external_identities"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Relationships
    account: Mapped["AccountTable"] = relationship("AccountTable", back_populates="external_identities")

    # Constraints: One provider user ID per provider
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_external_provider_user"),)

    def __repr__(self) -> str:
        return f"<ExternalIdentity(provider={self.provider}, user_id={self.provider_user_id})>"
