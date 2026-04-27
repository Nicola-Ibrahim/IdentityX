from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ......modules.accounts.application.account.service import AccountService
from ......modules.accounts.application.authentication.service import AuthenticationService
from ......modules.accounts.application.interfaces.token_errors import TokenError
from ......modules.accounts.infrastructure.configuration.containers import AccountsDIContainer
from .account_response import AccountResponse
from .logout_request import LogoutRequest
from .refresh_token_request import RefreshTokenRequest
from .register_account_request import RegisterAccountRequest
from .token_response import TokenResponse
from .update_account_request import UpdateAccountRequest
from .verify_account_request import VerifyAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


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
    try:
        # Service takes email and password strings
        _, dto = account_service.register(payload.email, payload.password)
        return AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/verify",
    response_model=AccountResponse,
    summary="Verify an account",
)
@inject
async def verify_account(
    payload: VerifyAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    try:
        # Service takes account_id string
        _, dto = account_service.verify(payload.account_id)
        return AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


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
    try:
        pair = auth_service.authenticate(form_data.username, form_data.password)
        return TokenResponse.from_dto(pair)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


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
    try:
        pair = auth_service.refresh_session(payload.refresh_token)
        return TokenResponse.from_dto(pair)
    except (TokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
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
    auth_service.logout(payload.refresh_token)


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
    dto = account_service.get_by_id(account_id)
    if not dto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return AccountResponse(
        id=dto.id,
        email=dto.email,
        is_verified=dto.is_verified,
        is_active=dto.is_active,
    )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Retrieve a single account",
)
@inject
async def get_account(
    account_id: str,
    _: str = Depends(get_current_account_id),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    dto = account_service.get_by_id(account_id)
    if not dto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return AccountResponse(
        id=dto.id,
        email=dto.email,
        is_verified=dto.is_verified,
        is_active=dto.is_active,
    )


@router.get(
    "/",
    response_model=list[AccountResponse],
    summary="List all accounts",
)
@inject
async def list_accounts(
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> list[AccountResponse]:
    dtos = account_service.list()
    return [
        AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        )
        for dto in dtos
    ]


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
    try:
        # Service takes account_id string and dict
        dto = account_service.update(account_id, payload.model_dump(exclude_unset=True))
        return AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an account",
)
@inject
async def delete_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> None:
    try:
        account_service.remove(account_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
