from datetime import datetime
from src.building_blocks.domain.events import DomainEvent


class SessionIssuedEvent(DomainEvent):
    session_id: str
    account_id: str
    refresh_token: str
    expires_at: datetime
