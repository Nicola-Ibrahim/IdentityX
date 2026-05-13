from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from ....accounts.application.queries.validate_token import ValidateTokenQuery
from ....accounts.domain.session.token_errors import TokenExpiredException
from ....accounts.infrastructure.module import AccountModule

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")


async def get_account_module(request: Request) -> AccountModule:
    """Dependency to get the AccountModule from app state."""
    return request.app.state.account_module


async def get_current_account_id(
    token: str = Depends(oauth2_scheme),
    account_module: AccountModule = Depends(get_account_module),
) -> str:
    """Validate Bearer token via the AccountModule.

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
