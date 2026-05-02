from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.modules.accounts.application.authentication.service import AuthenticationService
from src.modules.accounts.infrastructure.configuration.containers import AccountsDIContainer

router = APIRouter(tags=["discovery"])


@router.get("/.well-known/jwks.json", summary="Get JSON Web Key Set")
@inject
async def get_jwks(
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> dict:
    """
    Exposes the public key(s) in JWKS format for token verification by resource servers.
    """
    jwk = auth_service.get_public_key()
    return {"keys": [jwk]}
