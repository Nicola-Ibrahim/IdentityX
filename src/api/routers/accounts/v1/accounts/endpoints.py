from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.modules.accounts.application.account.dto import AccountDTO
from src.modules.accounts.application.account.service import AccountService
from src.modules.accounts.application.authentication.issue_token_pair_dto import IssuedTokenPairDTO
from src.modules.accounts.application.authentication.service import AuthenticationService
from src.modules.accounts.infrastructure.configuration.containers import AccountsDIContainer

from .....core.responses.success import APIResponse, ResponseEnvelope
from .....core.security.dependencies import get_current_account_id
from .logout_request import LogoutRequest
from .refresh_token_request import RefreshTokenRequest
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
)
@inject
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    result = await auth_service.authenticate(form_data.username, form_data.password)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/refresh",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Refresh access token",
)
@inject
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    result = await auth_service.refresh_session(payload.refresh_token)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


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
