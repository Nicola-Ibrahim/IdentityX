from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ......modules.accounts.application.interfaces.token_errors import (
    TokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from ......modules.accounts.infrastructure.configuration.containers import AccountsDIContainer
from ...modules.accounts.application.authentication.service import AuthenticationService


@inject
async def get_current_account_id(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> str:
    """Validate Bearer token via the DI-injected AuthenticationService.

    Maps domain exceptions to HTTP 401. No crypto code here.
    """
    try:
        return auth_service.get_current_account_id(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenError, TokenRevokedError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked token",
            headers={"WWW-Authenticate": "Bearer"},
        )
