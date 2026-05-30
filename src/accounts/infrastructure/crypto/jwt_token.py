import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization

from src.accounts.application.interfaces.jwt import TokenPayload, TokenService, ValidatedClaims
from src.accounts.domain.session.token_errors import (
    TokenExpiredException,
    TokenInvalidException,
)


class JWTTokenService(TokenService):
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

    def create_tokens(self, claims: TokenPayload) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        base_claims = claims.model_dump(exclude_none=True)

        access_token = self._create_access_token(base_claims, now)
        refresh_token = self._create_refresh_token(claims.sub, now)

        return access_token, refresh_token

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

    def validate_access_token(self, token: str) -> ValidatedClaims:
        claims = self.validate(token)
        if claims.typ != "access":
            raise TokenInvalidException(f"Token type mismatch: expected access, got {claims.typ}")
        return claims

    def validate_refresh_token(self, token: str) -> ValidatedClaims:
        claims = self.validate(token)
        if claims.typ != "refresh":
            raise TokenInvalidException(f"Token type mismatch: expected refresh, got {claims.typ}")
        return claims

    def create_mfa_token(self, claims: TokenPayload) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            **claims.model_dump(exclude_none=True),
            "iat": now,
            "exp": now + self._mfa_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "mfa",
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def validate_mfa_token(self, token: str) -> ValidatedClaims:
        claims = self.validate(token)
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
        # Load the public key using cryptography
        public_key = serialization.load_pem_public_key(self._public_key.encode())
        numbers = public_key.public_numbers()

        # Helper to base64url encode integers
        def to_base64url(val: int) -> str:
            # Convert integer to bytes
            byte_val = val.to_bytes((val.bit_length() + 7) // 8, byteorder="big")
            return base64.urlsafe_b64encode(byte_val).decode().rstrip("=")

        return {
            "kty": "RSA",
            "alg": self._algorithm,
            "use": "sig",
            "kid": "identityx-main-key",  # Stable ID for this key
            "n": to_base64url(numbers.n),
            "e": to_base64url(numbers.e),
        }
