import hashlib
import secrets

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate

from src.accounts.application.interfaces.account_module import BaseAccountModule
from src.accounts.application.session.commands.authenticate import AuthenticateCommand
from src.accounts.application.session.commands.authenticate_mfa import AuthenticateMfaCommand
from src.accounts.application.session.commands.logout import LogoutCommand
from src.accounts.application.session.commands.refresh_session import RefreshSessionCommand
from src.accounts.application.session.commands.social_authenticate import SocialAuthenticateCommand
from src.accounts.application.session.queries.get_social_auth_url import GetSocialAuthUrlQuery
from src.api.core.exceptions import APIError, raise_http
from src.api.core.responses import APIResponse, SuccessResponse
from src.api.core.security.dependencies import get_account_module
from src.api.routers.v1.auth.requests import MfaVerifyRequest
from src.api.routers.v1.auth.responses import AuthResponse, SocialAuthUrlResponse, TokenResponse

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/login",
    response_model=SuccessResponse[AuthResponse],
    summary="Login to an account",
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
    response_model=SuccessResponse[TokenResponse],
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


@router.post(
    "/token/mfa",
    response_model=SuccessResponse[AuthResponse],
    summary="Verify TOTP and issue tokens",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
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
    "/social/{provider}/url",
    response_model=SuccessResponse[SocialAuthUrlResponse],
    summary="Get social authentication URL",
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


@router.post(
    "/social/{provider}/callback",
    response_model=SuccessResponse[AuthResponse],
    summary="Handle social authentication callback",
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
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="invalid_oauth_state",
            message="Invalid OAuth state. Potential CSRF attack.",
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
