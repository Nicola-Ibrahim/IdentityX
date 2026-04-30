from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ......api.core.security.dependencies import get_current_account_id
from ......modules.accounts.application.account.service import AccountService
from ......modules.accounts.application.authentication.service import AuthenticationService
from ......modules.accounts.infrastructure.configuration.containers import AccountsDIContainer
from .account_response import AccountResponse
from .logout_request import LogoutRequest
from .refresh_token_request import RefreshTokenRequest
from .register_account_request import RegisterAccountRequest
from .token_response import TokenResponse
from .update_account_request import UpdateAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


def raise_http(e):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AccountResponse,
    summary="Register a new account",
)
@inject
async def register_account(
    payload: RegisterAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.register(payload.email, payload.password)
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/verify/{account_id}",
    response_model=AccountResponse,
    summary="Verify an account",
)
@inject
async def verify_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.verify(account_id)
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 compatible token login",
)
@inject
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> TokenResponse:
    result = await auth_service.authenticate(form_data.username, form_data.password)
    return result.match(on_success=TokenResponse.from_dto, on_failure=raise_http)


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
@inject
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> TokenResponse:
    result = await auth_service.refresh_session(payload.refresh_token)
    return result.match(on_success=TokenResponse.from_dto, on_failure=raise_http)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
)
@inject
async def logout(
    payload: LogoutRequest,
    _: str = Depends(get_current_account_id),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> None:
    result = await auth_service.logout(payload.refresh_token)
    result.match(on_success=lambda _: None, on_failure=raise_http)


@router.get(
    "/me",
    response_model=AccountResponse,
    summary="Retrieve the authenticated account",
)
@inject
async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.get_by_id(account_id)
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        ),
        on_failure=raise_http,
    )


@router.patch(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Update an account",
)
@inject
async def update_account(
    account_id: str,
    payload: UpdateAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.update(account_id, payload.model_dump(exclude_unset=True))
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        ),
        on_failure=raise_http,
    )
