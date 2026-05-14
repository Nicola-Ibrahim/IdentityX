from fastapi import APIRouter, Depends, status

from accounts.application.commands.activate_account import ActivateAccountCommand
from accounts.application.commands.deactivate_account import DeactivateAccountCommand
from accounts.application.commands.remove_account import RemoveAccountCommand
from accounts.application.commands.revoke_all_sessions import RevokeAllSessionsCommand
from accounts.application.interfaces.account_module import BaseAccountModule
from accounts.application.queries.get_account_by_id import GetAccountByIdQuery
from accounts.application.queries.list_accounts import ListAccountsQuery
from api.core.exceptions import raise_http
from api.core.responses import APIResponse, SuccessResponse
from api.core.security.dependencies import get_account_module, get_current_account_id
from api.core.utils.pagination import PaginationParams, get_pagination

from ..accounts.responses import AccountResponse

admin_router = APIRouter(
    prefix="/admin/accounts",
    tags=["admin-accounts"],
    dependencies=[Depends(get_current_account_id)],
)


@admin_router.get(
    "/",
    response_model=SuccessResponse[list[AccountResponse]],
    summary="List all accounts",
)
async def list_accounts(
    pagination: PaginationParams = Depends(get_pagination),
    account_module: BaseAccountModule = Depends(get_account_module),
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
    response_model=SuccessResponse[AccountResponse],
    summary="Suspend an account",
)
async def suspend_account(
    account_id: str,
    account_module: BaseAccountModule = Depends(get_account_module),
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
    response_model=SuccessResponse[AccountResponse],
    summary="Activate account",
)
async def activate_account(
    account_id: str,
    account_module: BaseAccountModule = Depends(get_account_module),
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
    account_module: BaseAccountModule = Depends(get_account_module),
) -> None:
    result = await account_module.execute(RevokeAllSessionsCommand(account_id=account_id))
    result.match(on_success=lambda _: None, on_failure=raise_http)


@admin_router.get(
    "/{account_id}",
    response_model=SuccessResponse[AccountResponse],
    summary="Get account details",
)
async def get_account(
    account_id: str,
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


@admin_router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an account",
)
async def delete_account(
    account_id: str,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> None:
    result = await account_module.execute(RemoveAccountCommand(account_id=account_id))
    result.match(on_success=lambda _: None, on_failure=raise_http)
