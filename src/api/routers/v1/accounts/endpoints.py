from fastapi import APIRouter, Depends, status
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate

from src.accounts.application.account.commands.register_account import RegisterAccountCommand
from src.accounts.application.account.commands.verify_account import VerifyAccountCommand
from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.api.core.exceptions import raise_http
from src.api.core.responses import APIResponse, SuccessResponse
from src.api.core.security.dependencies import get_account_module
from src.api.routers.v1.accounts.requests import RegisterAccountRequest
from src.api.routers.v1.accounts.responses import AccountResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[AccountResponse],
    summary="Register a new account",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
async def register_account(
    request: RegisterAccountRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(RegisterAccountCommand(email=request.email, password=request.password))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_201_CREATED,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/verify-email",
    response_model=SuccessResponse[AccountResponse],
    summary="Verify account email",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
async def verify_account(
    account_id: str,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(VerifyAccountCommand(account_id=account_id))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )
