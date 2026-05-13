from fastapi import APIRouter, Depends, HTTPException, status

from src.accounts.application.dtos.account import AuthDTO
from src.accounts.infrastructure.module import AccountModule
from src.api.core.security.dependencies import get_current_account_id, get_account_module
from src.api.core.utils.pagination import PaginationParams, get_pagination

from src.accounts.application.queries.list_accounts import ListAccountsQuery
from src.accounts.application.queries.get_account_by_id import GetAccountByIdQuery
from src.accounts.application.commands.deactivate import DeactivateAccountCommand
from src.accounts.application.commands.activate import ActivateAccountCommand
from src.accounts.application.commands.revoke_all_sessions import RevokeAllSessionsCommand
from src.accounts.application.commands.remove import RemoveAccountCommand

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
async def list_accounts(
    pagination: PaginationParams = Depends(get_pagination),
    account_module: AccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.query(ListAccountsQuery(limit=pagination.limit, offset=pagination.offset))

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
async def suspend_account(
    account_id: str,
    account_module: AccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(DeactivateAccountCommand(account_id=account_id))
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
async def activate_account(
    account_id: str,
    account_module: AccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(ActivateAccountCommand(account_id=account_id))
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
async def revoke_account_sessions(
    account_id: str,
    account_module: AccountModule = Depends(get_account_module),
) -> None:
    result = await account_module.execute(RevokeAllSessionsCommand(account_id=account_id))
    result.match(on_success=lambda _: None, on_failure=raise_http)


@admin_router.get(
    "/{account_id}",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Retrieve a single account",
)
async def get_account(
    account_id: str,
    account_module: AccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.query(GetAccountByIdQuery(account_id=account_id))
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
async def delete_account(
    account_id: str,
    account_module: AccountModule = Depends(get_account_module),
) -> None:
    result = await account_module.execute(RemoveAccountCommand(account_id=account_id))
    result.match(on_success=lambda _: None, on_failure=raise_http)
