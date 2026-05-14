import hashlib
import secrets

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate

from accounts.application.dtos.account import AccountDTO
from accounts.application.dtos.auth import (
    AuthDTO,
    MfaSetup,
    TokenPair,
)
from accounts.application.interfaces.account_module import BaseAccountModule
from api.core.responses.success import APIResponse, ResponseEnvelope
from api.core.security.dependencies import get_current_account_id, get_account_module

from accounts.application.commands.register_account import RegisterAccountCommand
from accounts.application.commands.verify_account import VerifyAccountCommand
from accounts.application.commands.authenticate import AuthenticateCommand
from accounts.application.commands.refresh_session import RefreshSessionCommand
from accounts.application.commands.logout import LogoutCommand
from accounts.application.commands.update_account import UpdateAccountCommand
from accounts.application.commands.setup_mfa import SetupMfaCommand
from accounts.application.commands.verify_and_enable_mfa import VerifyAndEnableMfaCommand
from accounts.application.commands.authenticate_mfa import AuthenticateMfaCommand
from accounts.application.commands.social_authenticate import SocialAuthenticateCommand

from accounts.application.queries.get_account_by_id import GetAccountByIdQuery
from accounts.application.queries.get_social_auth_url import GetSocialAuthUrlQuery

from .mfa_requests import MfaEnableRequest, MfaSetupRequest, MfaVerifyRequest
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
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
async def register_account(
    request: RegisterAccountRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(RegisterAccountCommand(email=request.email, password=request.password))
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
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
async def verify_account(
    account_id: str,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(VerifyAccountCommand(account_id=account_id))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token",
    response_model=ResponseEnvelope[AuthDTO],
    summary="OAuth2 compatible token login",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Hash the trusted device token from cookie if it exists
    device_token = request.cookies.get("trusted_device")
    device_hash = hashlib.sha256(device_token.encode()).hexdigest() if device_token else None

    result = await account_module.execute(
        AuthenticateCommand(
            email=form_data.username,
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent,
            device_hash=device_hash,
        )
    )

    if result.is_success:
        dto = result.value
        if not dto.requires_mfa and dto.tokens:
            response.set_cookie(
                key="refresh_token",
                value=dto.tokens.refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude_none=True),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/refresh",
    response_model=ResponseEnvelope[TokenPair],
    summary="Refresh access token",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(10, Duration.SECOND * 60))))],
)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    result = await account_module.execute(RefreshSessionCommand(refresh_token=refresh_token))

    if result.is_success:
        dto = result.value
        response.set_cookie(
            key="refresh_token",
            value=dto.refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
        )

        if dto.trusted_device_token:
            response.set_cookie(
                key="trusted_device",
                value=dto.trusted_device_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke refresh token",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(10, Duration.SECOND * 60))))],
)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    if refresh_token:
        await account_module.execute(LogoutCommand(refresh_token=refresh_token))
        response.delete_cookie("refresh_token")

    return APIResponse(
        data={"message": "Logged out successfully"},
        status_code=status.HTTP_200_OK,
    )


@router.get(
    "/me",
    response_model=ResponseEnvelope[AccountDTO],
    summary="Retrieve the authenticated account",
)
async def get_current_account(
    account_id: str = Depends(get_current_account_id),
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


@router.patch(
    "/me",
    response_model=ResponseEnvelope[AccountDTO],
    summary="Update the authenticated account",
)
async def update_account(
    request: UpdateAccountRequest,
    account_id: str = Depends(get_current_account_id),
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(
        UpdateAccountCommand(account_id=account_id, update_data=request.model_dump(exclude_unset=True))
    )
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/mfa/setup",
    response_model=ResponseEnvelope[MfaSetup],
    summary="Initiate MFA setup",
)
async def setup_mfa(
    request: MfaSetupRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    result = await account_module.execute(SetupMfaCommand(mfa_token=request.mfa_token))
    return result.match(
        on_success=lambda dto: APIResponse(data=dto.model_dump(), status_code=status.HTTP_200_OK),
        on_failure=raise_http,
    )


@router.post(
    "/mfa/enable",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Verify and enable MFA",
)
async def enable_mfa(
    fastapi_request: Request,
    response: Response,
    request: MfaEnableRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    result = await account_module.execute(
        VerifyAndEnableMfaCommand(
            mfa_token=request.mfa_token,
            totp_code=request.totp_code,
            secret=request.secret,
            recovery_codes=request.recovery_codes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )

    if result.is_success:
        dto = result.value
        if dto.tokens:
            response.set_cookie(
                key="refresh_token",
                value=dto.tokens.refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude_none=True),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/mfa",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Verify TOTP and issue tokens",
)
async def login_mfa(
    fastapi_request: Request,
    response: Response,
    request: MfaVerifyRequest,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    result = await account_module.execute(
        AuthenticateMfaCommand(
            mfa_token=request.mfa_token,
            totp_code=request.totp_code,
            recovery_code=request.recovery_code,
            ip_address=ip_address,
            user_agent=user_agent,
            trust_device=request.trust_device,
        )
    )

    if result.is_success:
        dto = result.value
        if dto.tokens:
            response.set_cookie(
                key="refresh_token",
                value=dto.tokens.refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude_none=True),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.get(
    "/social/{provider_name}/login",
    summary="Get Social OAuth2 Login URL",
)
async def social_login(
    provider_name: str,
    response: Response,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key=f"{provider_name}_auth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300,  # 5 minutes
    )

    result = await account_module.query(GetSocialAuthUrlQuery(provider_name=provider_name, state=state))

    return result.match(
        on_success=lambda url: APIResponse(data={"url": url}, status_code=status.HTTP_200_OK),
        on_failure=raise_http,
    )


@router.get(
    "/social/{provider_name}/callback",
    response_model=ResponseEnvelope[AuthDTO],
    summary="Social OAuth2 Callback",
)
async def social_callback(
    provider_name: str,
    fastapi_request: Request,
    response: Response,
    code: str,
    state: str,
    account_module: BaseAccountModule = Depends(get_account_module),
) -> APIResponse:
    stored_state = fastapi_request.cookies.get(f"{provider_name}_auth_state")
    if not stored_state or stored_state != state:
        return APIResponse(
            message="Invalid OAuth state. Potential CSRF attack.", status_code=status.HTTP_400_BAD_REQUEST
        )

    response.delete_cookie(f"{provider_name}_auth_state")

    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    result = await account_module.execute(
        SocialAuthenticateCommand(provider_name=provider_name, code=code, ip_address=ip_address, user_agent=user_agent)
    )

    if result.is_success:
        dto = result.value
        if dto.tokens:
            response.set_cookie(
                key="refresh_token",
                value=dto.tokens.refresh_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=30 * 24 * 60 * 60,
            )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude_none=True),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )
