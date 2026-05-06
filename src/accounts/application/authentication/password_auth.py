import hashlib
import uuid

from ....buckets.database.decorators import db
from ....building_blocks.domain.result import Result
from ...domain.account.value_objects.account_id import AccountId
from ...domain.account.value_objects.email import Email
from ...domain.interfaces.uow import BaseAsyncUnitOfWork
from ..audit.audit_action import AuditAction
from ..audit.service import AuditService
from ..interfaces.jwt import TokenPayload, TokenService
from ..interfaces.password_hasher import BasePasswordHasher
from .dtos import AuthDTO, MfaChallenge, MfaSetup, TokenPair
from .sessions import SessionService


class PasswordAuthenticationService:
    def __init__(
        self,
        uow: BaseAsyncUnitOfWork,
        password_hasher: BasePasswordHasher,
        sessions: SessionService,
        token_service: TokenService,
        audit_service: AuditService,
    ) -> None:
        self.uow = uow
        self._hasher = password_hasher
        self._sessions = sessions
        self._token_service = token_service
        self._audit = audit_service

    @Result.capture
    @db.transactional
    async def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        device_hash: str | None = None,
    ) -> AuthDTO:
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
            tokens = await self._sessions.issue_session(account, ip_address, user_agent)
            return AuthDTO(tokens=tokens)

        # Mandatory MFA check
        mfa_token = self._token_service.create_mfa_token(TokenPayload(sub=str(account.id.value)))

        # Log appropriate action
        log_action = AuditAction.MFA_REQUIRED if account.mfa.enabled else AuditAction.MFA_SETUP_INITIATED
        await self._audit.log(log_action, ip_address, user_agent, account_id=str(account.id.value))

        return AuthDTO(
            requires_mfa=True,
            mfa=MfaChallenge(mfa_token=mfa_token, mfa_setup_required=not account.mfa.enabled),
        )

    # --- MFA Operations ---

    @Result.capture
    @db.transactional
    async def setup_mfa(self, mfa_token: str) -> MfaSetup:
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

        return MfaSetup(secret=secret, provisioning_uri=provisioning_uri, recovery_codes=recovery_codes)

    @Result.capture
    @db.transactional
    async def verify_and_enable_mfa(
        self, mfa_token: str, totp_code: str, secret: str, recovery_codes: list[str], ip_address: str, user_agent: str
    ) -> AuthDTO:
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

        tokens = await self._sessions.issue_session(
            account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS
        )
        return AuthDTO(tokens=tokens)

    @Result.capture
    @db.transactional
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

        dto = await self._sessions.issue_session(account, ip_address, user_agent, action=AuditAction.LOGIN_SUCCESS)

        # We attach the raw token to the DTO so the API can set it as a cookie
        # We'll need to extend TokenPair or return it separately.
        # For simplicity, we'll return a tuple or just update the DTO.
        if new_device_token:
            dto.trusted_device_token = new_device_token

        return AuthDTO(tokens=dto)
