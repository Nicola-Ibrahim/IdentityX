from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
import secrets

from src.api.core.responses.success import APIResponse, ResponseEnvelope
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate
from src.api.core.security.dependencies import get_current_account_id
from src.accounts.application.account.dto import AccountDTO
from src.accounts.application.account.service import AccountService
from src.accounts.application.authentication.issue_token_pair_dto import IssuedTokenPairDTO
from src.accounts.application.authentication.service import AuthenticationService
from src.accounts.application.authentication.social_service import SocialAuthenticationService
from src.accounts.application.authentication.mfa_dto import MfaChallengeDTO, MfaSetupDTO
from src.accounts.infrastructure.configuration.containers import AccountsDIContainer

from .register_account_request import RegisterAccountRequest
from .update_account_request import UpdateAccountRequest
from .mfa_requests import MfaSetupRequest, MfaEnableRequest, MfaVerifyRequest
from fastapi import Request
import hashlib

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
@inject
async def register_account(
    request: RegisterAccountRequest,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.register(request.email, request.password)
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
@inject
async def verify_account(
    account_id: str,
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.verify(account_id)
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token",
    response_model=ResponseEnvelope[IssuedTokenPairDTO | MfaChallengeDTO],
    summary="OAuth2 compatible token login",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.SECOND * 60))))],
)
@inject
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Hash the trusted device token from cookie if it exists
    device_token = request.cookies.get("trusted_device")
    device_hash = hashlib.sha256(device_token.encode()).hexdigest() if device_token else None
    
    result = await auth_service.authenticate(
        form_data.username, 
        form_data.password,
        ip_address=ip_address,
        user_agent=user_agent,
        device_hash=device_hash
    )

    if result.is_success and isinstance(result.value, IssuedTokenPairDTO):
        dto = result.value
        # Set Refresh Token in a secure, HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=dto.refresh_token,
            httponly=True,
            secure=True,  # Set to True in production
            samesite="lax",
            max_age=30 * 24 * 60 * 60,  # 30 days
        )

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}) if isinstance(dto, IssuedTokenPairDTO) else dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/refresh",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Refresh access token",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(10, Duration.SECOND * 60))))],
)
@inject
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    result = await auth_service.refresh_session(refresh_token)

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
@inject
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None),
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    if refresh_token:
        await auth_service.logout(refresh_token)
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
@inject
async def get_current_account(
    account_id: str = Depends(get_current_account_id),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.get_by_id(account_id)
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
@inject
async def update_account(
    request: UpdateAccountRequest,
    account_id: str = Depends(get_current_account_id),
    account_service: AccountService = Depends(Provide[AccountsDIContainer.account_service]),
) -> APIResponse:
    result = await account_service.update(account_id, request.model_dump(exclude_unset=True))
    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )

@router.post(
    "/mfa/setup",
    response_model=ResponseEnvelope[MfaSetupDTO],
    summary="Initiate MFA setup",
)
@inject
async def setup_mfa(
    request: MfaSetupRequest,
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    result = await auth_service.setup_mfa(request.mfa_token)
    return result.match(
        on_success=lambda dto: APIResponse(data=dto.model_dump(), status_code=status.HTTP_200_OK),
        on_failure=raise_http,
    )


@router.post(
    "/mfa/enable",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Verify and enable MFA",
)
@inject
async def enable_mfa(
    fastapi_request: Request,
    response: Response,
    request: MfaEnableRequest,
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")
    
    result = await auth_service.verify_and_enable_mfa(
        request.mfa_token,
        request.totp_code,
        request.secret,
        request.recovery_codes,
        ip_address=ip_address,
        user_agent=user_agent
    )

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

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )


@router.post(
    "/token/mfa",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Verify TOTP and issue tokens",
)
@inject
async def login_mfa(
    fastapi_request: Request,
    response: Response,
    request: MfaVerifyRequest,
    auth_service: AuthenticationService = Depends(Provide[AccountsDIContainer.authentication_service]),
) -> APIResponse:
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")

    result = await auth_service.authenticate_mfa(
        mfa_token=request.mfa_token,
        totp_code=request.totp_code,
        recovery_code=request.recovery_code,
        ip_address=ip_address,
        user_agent=user_agent,
        trust_device=request.trust_device
    )

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

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )

import secrets
...
@router.get(
    "/social/{provider_name}/login",
    summary="Get Social OAuth2 Login URL",
)
@inject
async def social_login(
    provider_name: str,
    response: Response,
    social_service: SocialAuthenticationService = Depends(Provide[AccountsDIContainer.social_authentication_service]),
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
    
    result = await social_service.get_authorization_url(provider_name, state)
    
    return result.match(
        on_success=lambda url: APIResponse(data={"url": url}, status_code=status.HTTP_200_OK),
        on_failure=raise_http,
    )


@router.get(
    "/social/{provider_name}/callback",
    response_model=ResponseEnvelope[IssuedTokenPairDTO],
    summary="Social OAuth2 Callback",
)
@inject
async def social_callback(
    provider_name: str,
    fastapi_request: Request,
    response: Response,
    code: str,
    state: str,
    social_service: SocialAuthenticationService = Depends(Provide[AccountsDIContainer.social_authentication_service]),
) -> APIResponse:
    stored_state = fastapi_request.cookies.get(f"{provider_name}_auth_state")
    if not stored_state or stored_state != state:
        return APIResponse(
            message="Invalid OAuth state. Potential CSRF attack.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    response.delete_cookie(f"{provider_name}_auth_state")
    
    ip_address = fastapi_request.client.host if fastapi_request.client else "unknown"
    user_agent = fastapi_request.headers.get("user-agent", "unknown")
    
    result = await social_service.authenticate_callback(
        provider_name=provider_name,
        code=code,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
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

    return result.match(
        on_success=lambda dto: APIResponse(
            data=dto.model_dump(exclude={"refresh_token"}),
            status_code=status.HTTP_200_OK,
        ),
        on_failure=raise_http,
    )
