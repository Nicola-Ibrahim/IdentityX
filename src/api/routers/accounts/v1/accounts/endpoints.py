from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.api.core.responses.success import APIResponse, ResponseEnvelope
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate
from src.api.core.security.dependencies import get_current_account_id
from src.modules.accounts.application.account.dto import AccountDTO
from src.modules.accounts.application.account.service import AccountService
from src.modules.accounts.application.authentication.issue_token_pair_dto import IssuedTokenPairDTO
from src.modules.accounts.application.authentication.service import AuthenticationService
from src.modules.accounts.infrastructure.configuration.containers import AccountsDIContainer

from .register_account_request import RegisterAccountRequest
from .update_account_request import UpdateAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


def raise_http(e):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ResponseEnvelope[AccountDTO],
    summary="Register a new account",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
@inject
async def register_account(
    payload: RegisterAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.register(payload.email, payload.password)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_201_CREATED,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/verify/{account_id}",
    response_model=ResponseEnvelope[AccountDTO],
    summary="Verify an account",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
@inject
async def verify_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.verify(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="OAuth2 compatible token login",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
@inject
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    result = await auth_service.authenticate(form_data.username, form_data.password)

    if result.is_success:
        dto = result.value
        # Set Refresh Token in a secure, HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=dto.refresh_token,
            httponly=True,
            secure=True,  # Set to True in production
            samesite="lax",
            max_age=30 * 24 * 60 * 60,  # 30 days
        )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/refresh",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Refresh access token",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(10, Duration.SECOND * 60))))],
)
@inject
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    result = await auth_service.refresh_session(refresh_token)

    if result.is_success:
        dto = result.value
        response.set_cookie(
            key="refresh_token",
            value=dto.refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
        )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke refresh token",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(10, Duration.SECOND * 60))))],
)
@inject
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    if refresh_token:
        await auth_service.logout(refresh_token)
        response.delete_cookie("refresh_token")

    return APIResponse(
        data={"message": "Logged out successfully"},
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/me",
    response_model=ResponseEnvelope[AccountDTO],
    summary="Retrieve the authenticated account",
)
@inject
async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.get_by_id(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.patch(
    "/{account_id}",
    response_model=ResponseEnvelope[AccountDTO],
    summary="Update an account",
)
@inject
async def update_account(
    account_id: str,
    payload: UpdateAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.update(account_id, payload.model_dump(exclude_unset=True))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )
