import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from ...application.interfaces.jwt import JWTClaims, TokenFactory
from ...application.interfaces.token_errors import (
    TokenExpiredError,
    TokenInvalidError,
)


class JWTTokenFactory(TokenFactory):
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

    def create_tokens(self, claims: dict[str, Any]) -> tuple[str, str]:
        now = datetime.now(timezone.utc)

        # Access Token
        access_payload = {
            **claims,
            "iat": now,
            "exp": now + self._access_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "access",
        }
        access_token = jwt.encode(access_payload, self._private_key, algorithm=self._algorithm)

        # Refresh Token
        refresh_payload = {
            **claims,
            "iat": now,
            "exp": now + self._refresh_token_ttl,
            "jti": str(uuid.uuid4()),
            "iss": self._issuer,
            "typ": "refresh",
        }
        refresh_token = jwt.encode(refresh_payload, self._private_key, algorithm=self._algorithm)

        return access_token, refresh_token

    def validate_access_token(self, token: str) -> JWTClaims:
        return self._validate(token, expected_type="access")

    def validate_refresh_token(self, token: str) -> JWTClaims:
        return self._validate(token, expected_type="refresh")

    def _validate(self, token: str, expected_type: str) -> JWTClaims:
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError(f"Invalid token: {str(exc)}")

        if payload.get("typ") != expected_type:
            raise TokenInvalidError(f"Token type mismatch: expected {expected_type}")

        return JWTClaims.model_validate(payload)
