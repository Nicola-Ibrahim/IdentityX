from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.accounts.application.account.accounts import AccountService
from src.accounts.application.account.dtos.account import AuthDTO
from src.accounts.application.authentication.password_auth import PasswordAuthenticationService
from src.accounts.infrastructure.configuration.containers import AccountsDIContainer
from src.api.core.security.dependencies import get_current_account_id
from src.api.core.utils.pagination import PaginationParams, get_pagination

from ..core.responses.success import APIResponse, ResponseEnvelope

admin_router = APIRouter(
    prefix="/admin/accounts", tags=["admin-accounts"], dependencies=[Depends(get_current_account_id)]
)


def raise_http(e):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_router.get(
    "/",
    response_model=ResponseEnvelope[list[AuthDTO]],
    summary="List all accounts",
)
@inject
async def list_accounts(
    pagination: PaginationParams = Depends(get_pagination),
    accounts: AccountService = Depends(Provide[AccountsDIContainer.accounts]),
) -> APIResponse:
    result = await accounts.list(limit=pagination.limit, offset=pagination.offset)

    return result.match(
        on_success=lambda data: APIResponse(
            data=[dto.model_dump() for dto in data[0]],
            meta={
                "pagination": {
                    "total": data[1],
                    "limit": pagination.limit,
                    "offset": pagination.offset,
                }
            },
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@admin_router.post(
    "/{account_id}/suspend",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Suspend an account",
)
@inject
async def suspend_account(
    account_id: str,
    accounts: AccountService = Depends(Provide[AccountsDIContainer.accounts]),
) -> APIResponse:
    result = await accounts.deactivate(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@admin_router.post(
    "/{account_id}/activate",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Activate a suspended account",
)
@inject
async def activate_account(
    account_id: str,
    accounts: AccountService = Depends(Provide[AccountsDIContainer.accounts]),
) -> APIResponse:
    result = await accounts.activate(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@admin_router.post(
    "/{account_id}/revoke-sessions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke all sessions for an account",
)
@inject
async def revoke_account_sessions(
    account_id: str,
    auth_service: PasswordAuthenticationService = Depends(Provide[AccountsDIContainer.password_auth]),
) -> None:
    result = await auth_service.revoke_all_sessions(account_id)
    result.match(on_success=lambda _: None, on_failure=raise_http)


@admin_router.get(
    "/{account_id}",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Retrieve a single account",
)
@inject
async def get_account(
    account_id: str,
    accounts: AccountService = Depends(Provide[AccountsDIContainer.accounts]),
) -> APIResponse:
    result = await accounts.get_by_id(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@admin_router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an account",
)
@inject
async def delete_account(
    account_id: str,
    accounts: AccountService = Depends(Provide[AccountsDIContainer.accounts]),
) -> None:
    result = await accounts.remove(account_id)
    result.match(on_success=lambda _: None, on_failure=raise_http)
