from fastapi import APIRouter, Depends, status
from accounts.application.interfaces.account_module import BaseAccountModule
from accounts.application.queries.get_jwks import GetJwksQuery
from api.core.security.dependencies import get_account_module
from api.core.exceptions import raise_http
from api.core.responses import APIResponse, SuccessResponse
from .responses import JWKSResponse


router = APIRouter(prefix="", tags=["discovery"])


@router.get(
    "/.well-known/jwks.json", 
    response_model=SuccessResponse[JWKSResponse],
    summary="Get JSON Web Key Set"
)
async def get_jwks(
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    """
    Exposes the public key(s) in JWKS format for token verification.
    This follows the IdentityX Standard Response format.
    """
    result = await account_module.query(GetJwksQuery())

    return result.match(
        on_success=lambda jwk: APIResponse(
            data={"keys": [jwk]}, 
            status_code=status.HTTP_200_OK
        ),
        on_failure=raise_http,
    )
