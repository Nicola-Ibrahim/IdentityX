from typing import Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
import httpx

from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.accounts.application.session.queries.validate_token import ValidateTokenQuery
from src.accounts.domain.session.token_errors import TokenExpiredException
from src.api.core.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")


async def get_account_module(request: Request) -> BaseAccountModule:
    """Dependency to get the AccountModule from app state."""
    return request.app.state.account_module


async def get_current_token_claims(
    token: str = Depends(oauth2_scheme),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> dict[str, Any]:
    """Validate Bearer token and return all claims.

    Maps domain exceptions to HTTP 401.
    """
    result = await account_module.query(ValidateTokenQuery(token=token))

    if result.is_failure:
        error = result.error
        if isinstance(error, TokenExpiredException):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result.value


async def get_current_account_id(
    claims: dict[str, Any] = Depends(get_current_token_claims),
) -> str:
    """Get the current account ID from validated claims."""
    return claims["sub"]


async def check_opa_policy(
    request: Request,
    claims: dict[str, Any] = Depends(get_current_token_claims),
) -> None:
    """FastAPI dependency to authorize requests using OPA."""

    # 1. Extract subject attributes directly from token claims (no DTO/DB query)
    account_id = claims["sub"]
    roles = claims.get("roles") or []

    # 2. Build input context payload
    opa_input = {
        "input": {
            "subject": {
                "id": account_id,
                "roles": list(roles),
            },
            "action": request.method,
            "resource": {
                "path": request.url.path.strip("/").split("/"),
                "account_id": request.path_params.get("account_id"),
            },
            "context": {
                "ip_address": request.client.host if request.client else "unknown"
            }
        }
    }

    # 3. Post to OPA server
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(str(settings.OPA_URL), json=opa_input, timeout=2.0)
            response.raise_for_status()
            decision = response.json().get("result", False)
        except Exception as exc:
            # Fail-closed if the policy server is unreachable
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authorization policy check failed"
            ) from exc

    # 4. Enforce decision
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: insufficient permissions"
        )
