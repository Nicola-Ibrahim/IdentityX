from fastapi import APIRouter, Depends, HTTPException
from accounts.application.interfaces.account_module import BaseAccountModule
from accounts.application.queries.get_jwks import GetJwksQuery
from api.core.security.dependencies import get_account_module

router = APIRouter(tags=["discovery"])


def raise_http(e):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/.well-known/jwks.json", summary="Get JSON Web Key Set")
async def get_jwks(
    account_module: BaseAccountModule = Depends(get_account_module),
) -> dict:
    """
    Exposes the public key(s) in JWKS format for token verification by resource servers.
    """
    result = await account_module.query(GetJwksQuery())

    return result.match(
        on_success=lambda jwk: {"keys": [jwk]},
        on_failure=raise_http,
    )
