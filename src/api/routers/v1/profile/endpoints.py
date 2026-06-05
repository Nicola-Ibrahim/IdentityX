from fastapi import APIRouter, Depends, Request, Response, status

from src.accounts.application.account.commands.update_account import UpdateAccountCommand
from src.accounts.application.account.queries.get_account_by_id import GetAccountByIdQuery
from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.accounts.application.session.commands.setup_mfa import SetupMfaCommand
from src.accounts.application.session.commands.verify_and_enable_mfa import VerifyAndEnableMfaCommand
from src.api.core.exceptions import raise_http
from src.api.core.responses import APIResponse, SuccessResponse
from src.api.core.security.dependencies import get_account_module, get_current_account_id, check_opa_policy
from src.api.routers.v1.accounts.responses import AccountResponse
from src.api.routers.v1.auth.responses import AuthResponse
from src.api.routers.v1.profile.requests import MfaEnableRequest, MfaSetupRequest, UpdateAccountRequest
from src.api.routers.v1.profile.responses import MfaSetupResponse

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(check_opa_policy)],
)


@router.get(
    "/me",
    response_model=SuccessResponse[AccountResponse],
    summary="Get current account profile",
)
async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.query(GetAccountByIdQuery(account_id=account_id))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.patch(
    "/me",
    response_model=SuccessResponse[AccountResponse],
    summary="Update current account profile",
)
async def update_account(
    request: UpdateAccountRequest,
    account_id: str = Depends(get_current_account_id),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(
        UpdateAccountCommand(account_id=account_id, data=request.model_dump(exclude_unset=True))
    )
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/mfa/setup",
    response_model=SuccessResponse[MfaSetupResponse],
    summary="Initialize MFA setup",
)
async def setup_mfa(
    request: MfaSetupRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(SetupMfaCommand(mfa_token=request.mfa_token))
    return result.match(
        on_success=lambda dto: APIResponse(data=dto.model_dump(), status_code=status.HTTP_200_OK),
        on_failure=raise_http,
    )


@router.post(
    "/mfa/enable",
    response_model=SuccessResponse[AuthResponse],
    summary="Enable MFA for account",
)
async def enable_mfa(
    fastapi_request: Request,
    response: Response,
    request: MfaEnableRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    result = await account_module.execute(
        VerifyAndEnableMfaCommand(
            mfa_token=request.mfa_token,
            totp_code=request.totp_code,
            secret=request.secret,
            recovery_codes=request.recovery_codes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )

    if result.is_success:
        dto = result.value
        if dto.tokens:
            response.set_cookie(
                key="refresh_token",
                value=dto.tokens.refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude_none=True),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )
