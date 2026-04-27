from abc import ABC, abstractmethod
from datetime import datetime


class TokenDenylistRepository(ABC):
    """Interface for managing revoked JWT tokens."""

    @abstractmethod
    def add(self, jti: str, expires_at: datetime) -> None:
        """Add a JTI to the denylist with its expiration time."""
        pass

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Check if a JTI is in the denylist."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired tokens from the denylist. Returns count of removed items."""
        pass
