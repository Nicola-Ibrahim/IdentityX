from datetime import datetime, timedelta, timezone

from accounts.domain.audit.audit_action import AuditAction
from accounts.domain.session.session import Session
from accounts.domain.session.value_objects.refresh_token import RefreshToken
from accounts.domain.session.value_objects.session_id import SessionId
from accounts.application.dtos.auth import TokenPair
from accounts.application.interfaces.jwt import TokenPayload


async def issue_session(
    account,
    ip_address: str,
    user_agent: str,
    token_service,
    session_repo,
    audit_repo,
    audit_service,
    action: AuditAction = AuditAction.LOGIN_SUCCESS,
    session_ttl: timedelta = None,
) -> TokenPair:
    """Helper to issue a new session and JWT token pair."""
    session_id = SessionId.create()
    session_ttl = session_ttl or timedelta(hours=12)
    expires_at = datetime.now(timezone.utc) + session_ttl

    access, refresh = token_service.create_tokens(TokenPayload(sub=str(account.id.value), sid=str(session_id.value)))

    session = Session.issue(
        account_id=account.id,
        refresh_token=RefreshToken.create(refresh),
        expires_at=expires_at,
        session_id=session_id,
    )

    await session_repo.add(session)
    audit_entry = audit_service.create_entry(action, ip_address, user_agent, account_id=str(account.id.value))
    await audit_repo.add(audit_entry)

    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=int(session_ttl.total_seconds()),
    )
