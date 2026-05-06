from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.accounts.application.authentication.sessions import SessionService
from src.accounts.infrastructure.configuration.containers import AccountsDIContainer

router = APIRouter(tags=["discovery"])


@router.get("/.well-known/jwks.json", summary="Get JSON Web Key Set")
@inject
async def get_jwks(
    sessions: SessionService = Depends(Provide[AccountsDIContainer.sessions]),
) -> dict:
    """
    Exposes the public key(s) in JWKS format for token verification by resource servers.
    """
    jwk = sessions.get_public_key()
    return {"keys": [jwk]}
