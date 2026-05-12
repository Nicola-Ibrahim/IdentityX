import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from .....building_blocks.domain.result import Result
from ....domain.account.account import Account
from ....domain.account.value_objects.account_id import AccountId
from ....domain.account.value_objects.email import Email
from ....domain.audit.audit_action import AuditAction
from ....domain.interfaces.account_repository import BaseAccountRepository
from ....domain.interfaces.session_repository import BaseSessionRepository
from ....domain.interfaces.audit_repository import BaseAuditRepository
from ....domain.services.audit_service import AuditService
from ....domain.session.session import Session
from ....domain.session.value_objects.refresh_token import RefreshToken
from ....domain.session.value_objects.session_id import SessionId
from ...interfaces.jwt import TokenPayload, TokenService
from ...interfaces.password_hasher import BasePasswordHasher
from .dtos import AuthDTO, MfaChallenge, MfaSetup, TokenPair

class PasswordAuthenticationService:
    def __init__(
        self,
        account_repo: BaseAccountRepository,
        session_repo: BaseSessionRepository,
        audit_repo: BaseAuditRepository,
        password_hasher: BasePasswordHasher,
        token_service: TokenService,
        audit_service: AuditService,
    ) -> None:
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._audit_repo = audit_repo
        self._hasher = password_hasher
        self._token_service = token_service
        self._audit = audit_service

    async def _issue_session(
        self, account: Account, ip_address: str, user_agent: str, action: AuditAction = AuditAction.LOGIN_SUCCESS
    ) -> TokenPair:
        """Internal helper to issue a new session and JWT token pair."""
        session_id = SessionId.create()
        # Default TTL of 12 hours, same as SessionService
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)

        access, refresh = self._token_service.create_tokens(
            TokenPayload(sub=str(account.id.value), sid=str(session_id.value))
        )

        session = Session.issue(
            account_id=account.id,
            refresh_token=RefreshToken.create(refresh),
            expires_at=expires_at,
            session_id=session_id,
        )

        await self._session_repo.add(session)
        audit_entry = self._audit.create_entry(action, ip_address, user_agent, account_id=str(account.id.value))
        await self._audit_repo.add(audit_entry)

        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=12 * 3600,
        )

    @Result.capture
    async def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        device_hash: str | None = None,
    ) -> AuthDTO:
        """Authenticate user and either issue tokens or an MFA challenge."""
        account = await self._account_repo.get_by_email(str(Email.create(email)))

        if not account:
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED, ip_address, user_agent, details={"email": email, "reason": "user_not_found"}
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid credentials")

        if not self._hasher.verify(password, account.password.value):
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "invalid_password"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid credentials")

        if not account.can_login():
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "account_inactive_or_unverified"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Account not active or verified")

        # Check for trusted device (Phase 4 logic)
        if device_hash and account.is_device_trusted(device_hash):
            audit_entry = self._audit.create_entry(
                AuditAction.LOGIN_SUCCESS,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"trusted_device": True},
            )
            await self._audit_repo.add(audit_entry)
            tokens = await self._issue_session(account, ip_address, user_agent)
            return AuthDTO(tokens=tokens)

        # Mandatory MFA check
        mfa_token = self._token_service.create_mfa_token(TokenPayload(sub=str(account.id.value)))

        # Log appropriate action
        log_action = AuditAction.MFA_REQUIRED if account.mfa.enabled else AuditAction.MFA_SETUP_INITIATED
        audit_entry = self._audit.create_entry(log_action, ip_address, user_agent, account_id=str(account.id.value))
        await self._audit_repo.add(audit_entry)

        return AuthDTO(
            requires_mfa=True,
            mfa=MfaChallenge(mfa_token=mfa_token, mfa_setup_required=not account.mfa.enabled),
        )

    @Result.capture
    async def setup_mfa(self, mfa_token: str) -> MfaSetup:
        """Generate a new MFA secret and provisioning URI."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=str(account.email), issuer_name="IdentityX")

        # In a real app, we'd pre-generate recovery codes here too
        recovery_codes = [str(uuid.uuid4())[:8] for _ in range(8)]

        return MfaSetup(secret=secret, provisioning_uri=provisioning_uri, recovery_codes=recovery_codes)

    @Result.capture
    async def verify_and_enable_mfa(
        self, mfa_token: str, totp_code: str, secret: str, recovery_codes: list[str], ip_address: str, user_agent: str
    ) -> AuthDTO:
        """Verify the first TOTP code and enable MFA for the account."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        totp = pyotp.TOTP(secret)
        if not totp.verify(totp_code):
            audit_entry = self._audit.create_entry(
                AuditAction.MFA_FAILED,
                ip_address,
                user_agent,
                account_id=str(account.id.value),
                details={"reason": "invalid_totp_during_setup"},
            )
            await self._audit_repo.add(audit_entry)
            raise ValueError("Invalid TOTP code")

        # Hashing recovery codes before saving is best practice
        # For simplicity in this demo, we save them as-is (but they should be hashed)
        account.enable_mfa(secret, recovery_codes)
        await self._account_repo.update(account)

        audit_entry = self._audit.create_entry(
            AuditAction.MFA_ENABLED, ip_address, user_agent, account_id=str(account.id.value)
        )
        await self._audit_repo.add(audit_entry)

        tokens = await self._issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)
        return AuthDTO(tokens=tokens)

    @Result.capture
    async def authenticate_mfa(
        self,
        mfa_token: str,
        ip_address: str,
        user_agent: str,
        totp_code: str | None = None,
        recovery_code: str | None = None,
        trust_device: bool = False,
    ) -> AuthDTO:
        """Verify TOTP code and issue final tokens."""
        import pyotp

        claims = self._token_service.validate_mfa_token(mfa_token)
        account = await self._account_repo.get_by_id(AccountId.create(uuid.UUID(claims.sub)))
        if not account:
            raise ValueError("Account not found")

        if not account.mfa.enabled or not account.mfa.secret:
            raise ValueError("MFA not enabled for this account")

        # Try recovery code first if provided
        mfa_verified = False
        if recovery_code:
            mfa_verified = account.consume_recovery_code(recovery_code)
            if not mfa_verified:
                audit_entry = self._audit.create_entry(
                    AuditAction.MFA_FAILED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_recovery_code"},
                )
                await self._audit_repo.add(audit_entry)
                raise ValueError("invalid_recovery_code")

        # Then try TOTP
        elif totp_code:
            totp = pyotp.TOTP(account.mfa.secret)
            if totp.verify(totp_code):
                mfa_verified = True
            else:
                audit_entry = self._audit.create_entry(
                    AuditAction.MFA_FAILED,
                    ip_address,
                    user_agent,
                    account_id=str(account.id.value),
                    details={"reason": "invalid_totp"},
                )
                await self._audit_repo.add(audit_entry)
                raise ValueError("invalid_totp")

        else:
            raise ValueError("Either TOTP code or recovery code must be provided")

        audit_entry = self._audit.create_entry(
            AuditAction.MFA_VERIFIED, ip_address, user_agent, account_id=str(account.id.value)
        )
        await self._audit_repo.add(audit_entry)

        # Phase 4: Trust device logic
        new_device_token = None
        if trust_device:
            new_device_token = str(uuid.uuid4())
            device_hash = hashlib.sha256(new_device_token.encode()).hexdigest()
            account.trust_device(device_hash, user_agent, ip_address)
            await self._account_repo.update(account)
            audit_entry = self._audit.create_entry(
                AuditAction.TRUSTED_DEVICE_ADDED, ip_address, user_agent, account_id=str(account.id.value)
            )
            await self._audit_repo.add(audit_entry)

        dto = await self._issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)

        if new_device_token:
            dto.trusted_device_token = new_device_token

        return AuthDTO(tokens=dto)
