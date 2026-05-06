from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.accounts.application.interfaces.token_errors import (
    TokenError,
    TokenExpiredError,
    TokenRevokedError,
)
from src.accounts.infrastructure.configuration.containers import AccountsDIContainer
from src.accounts.application.authentication.sessions import SessionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")


@inject
async def get_current_account_id(
    token: str = Depends(oauth2_scheme),
    sessions: SessionService = Depends(Provide[AccountsDIContainer.sessions]),
) -> str:
    """Validate Bearer token via the DI-injected SessionService.

    Maps domain exceptions to HTTP 401. No crypto code here.
    """
    try:
        return sessions.get_current_account_id(token)
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
