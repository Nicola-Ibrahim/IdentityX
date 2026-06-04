import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pydantic import BaseModel, Field

from src.accounts.domain.session.token_errors import (
    TokenExpiredException,
    TokenInvalidException,
)
from src.accounts.domain.session.value_objects.access_token import AccessToken
from src.accounts.domain.session.value_objects.mfa_token import MfaToken
from src.accounts.domain.session.value_objects.refresh_token import RefreshToken


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
        return datetime.fromtimestamp(self.exp, tz=timezone.utc)


class TokenService:
    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str = "RS256",
        issuer: str = "identityx",
        access_token_ttl_minutes: int = 15,
        refresh_token_ttl_days: int = 7,
    ) -> None:
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm
        self._issuer = issuer
        self._access_token_ttl = timedelta(minutes=access_token_ttl_minutes)
        self._refresh_token_ttl = timedelta(days=refresh_token_ttl_days)
        self._mfa_token_ttl = timedelta(minutes=5)

    def create_tokens(self, claims: TokenPayload) -> tuple[AccessToken, RefreshToken]:
        now = datetime.now(timezone.utc)
        base_claims = claims.model_dump(exclude_none=True)

        access_token_str = self._create_access_token(base_claims, now)
        refresh_token_str = self._create_refresh_token(claims.sub, now)

        return AccessToken.create(access_token_str), RefreshToken.create(refresh_token_str)

    def _create_access_token(self, base_claims: dict[str, Any], now: datetime) -> str:
        payload = {
            **base_claims,
            "iat": now,
            "exp": now + self._access_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "access",
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def _create_refresh_token(self, sub: str, now: datetime) -> str:
        payload = {
            "sub": sub,
            "iat": now,
            "exp": now + self._refresh_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "refresh",
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def validate_access_token(self, token: AccessToken) -> ValidatedClaims:
        claims = self.validate(token.value)
        if claims.typ != "access":
            raise TokenInvalidException(f"Token type mismatch: expected access, got {claims.typ}")
        return claims

    def validate_refresh_token(self, token: RefreshToken) -> ValidatedClaims:
        claims = self.validate(token.value)
        if claims.typ != "refresh":
            raise TokenInvalidException(f"Token type mismatch: expected refresh, got {claims.typ}")
        return claims

    def create_mfa_token(self, claims: TokenPayload) -> MfaToken:
        now = datetime.now(timezone.utc)
        payload = {
            **claims.model_dump(exclude_none=True),
            "iat": now,
            "exp": now + self._mfa_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "mfa",
        }
        return MfaToken.create(jwt.encode(payload, self._private_key, algorithm=self._algorithm))

    def validate_mfa_token(self, token: MfaToken) -> ValidatedClaims:
        claims = self.validate(token.value)
        if claims.typ != "mfa":
            raise TokenInvalidException(f"Token type mismatch: expected mfa, got {claims.typ}")
        return claims

    def validate(self, token: str) -> ValidatedClaims:
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
            )
            return ValidatedClaims(**payload)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Token has expired")
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidException(f"Invalid token: {str(exc)}")

    def get_public_key_jwk(self) -> dict:
        """Return the public key in JSON Web Key format."""
        from cryptography.hazmat.primitives import serialization

        # Load public key using cryptography
        public_key = serialization.load_pem_public_key(self._public_key.encode())

        # Generate JWK via pyjwt native functionality
        alg = jwt.algorithms.RSAAlgorithm(jwt.algorithms.RSAAlgorithm.SHA256)
        jwk = alg.to_jwk(public_key)
        
        # Merge standard key id and usage fields
        return {
            **jwk,
            "use": "sig",
            "kid": "identityx-main-key",  # Stable ID for this key
        }
