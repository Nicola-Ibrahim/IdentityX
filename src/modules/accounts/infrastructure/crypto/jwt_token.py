import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from ...application.interfaces.jwt import TokenPayload, TokenService, ValidatedClaims
from ...application.interfaces.token_errors import (
    TokenExpiredError,
    TokenInvalidError,
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
            raise TokenInvalidError(f"Token type mismatch: expected access, got {claims.typ}")
        return claims

    def validate_refresh_token(self, token: str) -> ValidatedClaims:
        claims = self.validate(token)
        if claims.typ != "refresh":
            raise TokenInvalidError(f"Token type mismatch: expected refresh, got {claims.typ}")
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
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"Invalid token: {str(exc)}")
