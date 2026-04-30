from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from ......api.core.responses.success import APIResponse
from ......api.core.utils.pagination import PaginationParams, get_pagination
from ......modules.accounts.application.account.service import AccountService
from ......modules.accounts.application.authentication.service import AuthenticationService
from ......modules.accounts.infrastructure.configuration.containers import AccountsDIContainer
from ..accounts.account_response import AccountResponse

admin_router = APIRouter(prefix="/admin/accounts", tags=["admin-accounts"])


def raise_http(e):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@admin_router.get(
    "/",
    summary="List all accounts",
)
@inject
async def list_accounts(
    pagination: PaginationParams = Depends(get_pagination),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.list(limit=pagination.limit, offset=pagination.offset)

    return result.match(
        on_success=lambda data: APIResponse(
            data=[
                AccountResponse(
                    id=dto.id,
                    email=dto.email,
                    is_verified=dto.is_verified,
                    is_active=dto.is_active,
                )
                for dto in data[0]
            ],
            meta={
                "pagination": {
                    "total": data[1],
                    "limit": pagination.limit,
                    "offset": pagination.offset,
                }
            },
        ),
        on_failure=raise_http,
    )


@admin_router.post(
    "/{account_id}/suspend",
    response_model=AccountResponse,
    summary="Suspend an account",
)
@inject
async def suspend_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.deactivate(account_id)
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
        ),
        on_failure=raise_http,
    )


@admin_router.post(
    "/{account_id}/activate",
    response_model=AccountResponse,
    summary="Activate a suspended account",
)
@inject
async def activate_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> AccountResponse:
    result = await account_service.activate(account_id)
    return result.match(
        on_success=lambda dto: AccountResponse(
            id=dto.id,
            email=dto.email,
            is_verified=dto.is_verified,
            is_active=dto.is_active,
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
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> None:
    result = await auth_service.revoke_all_sessions(account_id)
    result.match(on_success=lambda _: None, on_failure=raise_http)


@admin_router.get(
    "/{account_id}",
    response_model=AccountResponse,
    summary="Retrieve a single account",
)
@inject
async def get_account(
    account_id: str,
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


@admin_router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an account",
)
@inject
async def delete_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> None:
    result = await account_service.remove(account_id)
    result.match(on_success=lambda _: None, on_failure=raise_http)
