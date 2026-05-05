from abc import ABC, abstractmethod
from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Basic claims required to issue a token pair."""

    sub: str = Field(..., description="Subject (account_id)")
    sid: str | None = Field(None, description="Session ID")


class ValidatedClaims(BaseModel):
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


class TokenService(ABC):
    """Abstract interface for modern RS256 JWT operations."""

    @abstractmethod
    def create_tokens(self, claims: TokenPayload) -> tuple[str, str]:
        """Create an (access_token, refresh_token) pair."""
        pass

    @abstractmethod
    def validate(self, token: str) -> ValidatedClaims:
        """Validate any JWT token and return its claims."""
        pass

    @abstractmethod
    def validate_access_token(self, token: str) -> ValidatedClaims:
        """Validate an access token and return claims."""
        pass

    @abstractmethod
    def validate_refresh_token(self, token: str) -> ValidatedClaims:
        """Validate a refresh token and return claims."""
        pass

    @abstractmethod
    def create_mfa_token(self, claims: TokenPayload) -> str:
        """Issue a short-lived JWT with typ='mfa'."""
        pass

    @abstractmethod
    def validate_mfa_token(self, token: str) -> ValidatedClaims:
        """Validate an MFA token and return claims."""
        pass

    @abstractmethod
    def get_public_key_jwk(self) -> dict:
        """Return the public key in JSON Web Key format."""
        pass
