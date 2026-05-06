import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from ....buckets.database.decorators import transactional
from ....building_blocks.domain.result import Result
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ...domain.session.session import Session
from ...domain.session.value_objects.refresh_token import RefreshToken
from ...domain.session.value_objects.session_id import SessionId
from ..audit.audit_action import AuditAction
from ..audit.service import AuditService
from ..interfaces.jwt import TokenPayload, TokenService
from ..interfaces.password_hasher import BasePasswordHasher
from .issue_token_pair_dto import IssuedTokenPairDTO
from .mfa_dto import MfaChallengeDTO, MfaSetupDTO


class AuthenticationService:
    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        password_hasher: BasePasswordHasher,
        token_service: TokenService,
        audit_service: AuditService,
        session_ttl: timedelta | None = None,
    ) -> None:
        self.uow = uow
        self._hasher = password_hasher
        self._token_service = token_service
        self._audit = audit_service
        self._session_ttl = session_ttl or timedelta(hours=12)

    @Result.capture
    @transactional
    async def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        device_hash: str | None = None,
    ) -> IssuedTokenPairDTO | MfaChallengeDTO:
        """Authenticate user and either issue tokens or an MFA challenge."""
        account = await self.uow.accounts.get_by_email(str(Email.create(email)))

        if not account:
            await self._audit.log(
                AuditAction.LOGIN_FAILED, ip_address, user_agent, details={"email": email, "reason": "user_not_found"}
            )
            raise ValueError("Invalid credentials")

        if not self._hasher.verify(password, account.password.value if account.password else ""):
            await self._audit.log(
                AuditAction.LOGIN_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "invalid_password"},
            )
            raise ValueError("Invalid credentials")

        if not account.can_login():
            await self._audit.log(
                AuditAction.LOGIN_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "account_inactive_or_unverified"},
            )
            raise ValueError("Account not active or verified")

        # Check for trusted device (Phase 4 logic)
        if device_hash and account.is_device_trusted(device_hash):
            await self._audit.log(
                AuditAction.LOGIN_SUCCESS,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"trusted_device": True},
            )
            return await self._issue_session(account, ip_address, user_agent)

        # Mandatory MFA check
        mfa_token = self._token_service.create_mfa_token(TokenPayload(sub=str(account.id.value)))

        # Log appropriate action
        log_action = AuditAction.MFA_REQUIRED if account.mfa.enabled else AuditAction.MFA_SETUP_INITIATED
        await self._audit.log(log_action, ip_address, user_agent, account_id=str(account.id.value))

        return MfaChallengeDTO(mfa_token=mfa_token, mfa_setup_required=not account.mfa.enabled)

    async def _issue_session(
        self, account: Any, ip_address: str, user_agent: str, action: AuditAction = AuditAction.LOGIN_SUCCESS
    ) -> IssuedTokenPairDTO:
        """Internal helper to issue a session and tokens."""
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        access, refresh = self._token_service.create_tokens(
            TokenPayload(sub=str(account.id.value), sid=str(session_id.value))
        )

        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self.uow.sessions.add(session)
        await self._audit.log(action, ip_address, user_agent, account_id=str(account.id.value))

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    @Result.capture
    @transactional
    async def refresh_session(self, refresh_token_str: str) -> IssuedTokenPairDTO:
        """Rotate tokens using a valid refresh token."""
        # 1. Validate JWT structure and signature
        claims = self._token_service.validate_refresh_token(refresh_token_str)

        # 2. Load and validate domain session
        session = await self.uow.sessions.get_by_refresh_token(RefreshToken.create(refresh_token_str))

        if not session:
            raise ValueError("Session not found")

        if not session.is_active or session.is_revoked:
            raise ValueError("Session is no longer active or has been revoked")

        if session.is_expired():
            raise ValueError("Session has expired")

        # 3. Revoke old session (single-use rotation)
        session.revoke()
        await self.uow.sessions.update(session)

        # 4. Issue new session and tokens
        result = await self.authenticate_by_id(claims.sub)
        return result

    @Result.capture
    @transactional
    async def authenticate_by_id(self, account_id: str) -> IssuedTokenPairDTO:
        """Issue tokens for an already verified account (internal use)."""
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(account_id)))
        if not account:
            raise ValueError("Account not found")

        # 1. Prepare session metadata
        session_id = SessionId.create()
        expires_at = datetime.now(timezone.utc) + self._session_ttl

        # 2. Issue JWT tokens
        access, refresh = self._token_service.create_tokens(TokenPayload(sub=account_id, sid=str(session_id.value)))

        # 3. Create domain session
        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self.uow.sessions.add(session)

        return IssuedTokenPairDTO(
            access_token=access,
            refresh_token=refresh,
            expires_in=int(self._session_ttl.total_seconds()),
        )

    @Result.capture
    @transactional
    async def logout(self, refresh_token_str: str) -> None:
        """Revoke a session based on the refresh token."""
        try:
            self._token_service.validate_refresh_token(refresh_token_str)

            # Revoke domain session
            session = await self.uow.sessions.get_by_refresh_token(RefreshToken.create(refresh_token_str))
            if session:
                session.revoke()
                await self.uow.sessions.update(session)
        except Exception:
            # Logout should be silent if token is already invalid
            pass

    @Result.capture
    @transactional
    async def revoke_all_sessions(self, account_id: str) -> None:
        """Forcefully revoke all active sessions for an account."""
        account_id_vo = AccountId.create(uuid.UUID(account_id))
        await self.uow.sessions.revoke_all_for_account(account_id_vo)

    def get_current_account_id(self, access_token_str: str) -> str:
        """Validate an access token and return the account ID."""
        claims = self._token_service.validate_access_token(access_token_str)
        return claims.sub

    def get_public_key(self) -> dict:
        """Return the public key in JWK format."""
        return self._token_service.get_public_key_jwk()

    # --- MFA Operations ---

    @Result.capture
    @transactional
    async def setup_mfa(self, mfa_token: str) -> MfaSetupDTO:
        """Generate a new MFA secret and provisioning URI."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=str(account.email), issuer_name="IdentityX")

        # In a real app, we'd pre-generate recovery codes here too
        recovery_codes = [str(uuid.uuid4())[:8] for _ in range(8)]

        return MfaSetupDTO(secret=secret, provisioning_uri=provisioning_uri, recovery_codes=recovery_codes)

    @Result.capture
    @transactional
    async def verify_and_enable_mfa(
        self, mfa_token: str, totp_code: str, secret: str, recovery_codes: list[str], ip_address: str, user_agent: str
    ) -> IssuedTokenPairDTO:
        """Verify the first TOTP code and enable MFA for the account."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        totp = pyotp.TOTP(secret)
        if not totp.verify(totp_code):
            await self._audit.log(
                AuditAction.MFA_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "invalid_totp_during_setup"},
            )
            raise ValueError("Invalid TOTP code")

        # Hashing recovery codes before saving is best practice
        # For simplicity in this demo, we save them as-is (but they should be hashed)
        account.enable_mfa(secret, recovery_codes)
        await self.uow.accounts.update(account)

        await self._audit.log(AuditAction.MFA_ENABLED, ip_address, user_agent, account_id=str(account.id.value))

        return await self._issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)

    @Result.capture
    @transactional
    async def authenticate_mfa(
        self,
        mfa_token: str,
        ip_address: str,
        user_agent: str,
        totp_code: str | None = None,
        recovery_code: str | None = None,
        trust_device: bool = False,
    ) -> IssuedTokenPairDTO:
        """Verify TOTP code and issue final tokens."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self.uow.accounts.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        if not account.mfa.enabled or not account.mfa.secret:
            raise ValueError("MFA not enabled for this account")

        # Try recovery code first if provided
        mfa_verified = False
        if recovery_code:
            mfa_verified = account.consume_recovery_code(recovery_code)
            if not mfa_verified:
                await self._audit.log(
                    AuditAction.MFA_FAILED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_recovery_code"},
                )
                raise ValueError("invalid_recovery_code")

        # Then try TOTP
        elif totp_code:
            totp = pyotp.TOTP(account.mfa.secret)
            if totp.verify(totp_code):
                mfa_verified = True
            else:
                await self._audit.log(
                    AuditAction.MFA_FAILED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_totp"},
                )
                raise ValueError("invalid_totp")

        else:
            raise ValueError("Either TOTP code or recovery code must be provided")

        await self._audit.log(AuditAction.MFA_VERIFIED, ip_address, user_agent, account_id=str(account.id.value))

        # Phase 4: Trust device logic
        new_device_token = None
        if trust_device:
            new_device_token = str(uuid.uuid4())
            device_hash = hashlib.sha256(new_device_token.encode()).hexdigest()
            account.trust_device(device_hash, user_agent, ip_address)
            await self.uow.accounts.update(account)
            await self._audit.log(
                AuditAction.TRUSTED_DEVICE_ADDED, ip_address, user_agent, account_id=str(account.id.value)
            )

        dto = await self._issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)

        # We attach the raw token to the DTO so the API can set it as a cookie
        # We'll need to extend IssuedTokenPairDTO or return it separately.
        # For simplicity, we'll return a tuple or just update the DTO.
        if new_device_token:
            dto.trusted_device_token = new_device_token

        return dto
