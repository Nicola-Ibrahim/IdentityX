from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


from pydantic import BaseModel, Field


class JWTClaims(BaseModel):
    """Modern Pydantic model for JWT payload validation."""

    sub: str = Field(..., description="Subject (account_id)")
    sid: str | None = Field(None, description="Session ID")
    jti: str = Field(..., description="Unique token identifier")
    exp: int = Field(..., description="Expiration timestamp (Unix)")
    iat: int = Field(..., description="Issued at timestamp (Unix)")
    typ: str = Field(..., description="Token type: 'access' or 'refresh'")
    iss: str | None = Field(None, description="Issuer identifier")

    @property
    def exp_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.exp)


class TokenFactory(ABC):
    """Abstract interface for modern RS256 JWT operations."""

    @abstractmethod
    def create_tokens(self, claims: dict[str, Any]) -> tuple[str, str]:
        """Create an (access_token, refresh_token) pair."""
        pass

    @abstractmethod
    def validate_access_token(self, token: str) -> JWTClaims:
        """Validate an access token and return claims.
        Raises TokenError subtypes on failure.
        """
        pass

    @abstractmethod
    def validate_refresh_token(self, token: str) -> JWTClaims:
        """Validate a refresh token and return claims.
        Raises TokenError subtypes on failure.
        """
        pass
