import json
from datetime import datetime, timezone
from typing import Iterable

import redis.asyncio as redis

from src.accounts.domain.session.repositories.session_repository import BaseSessionRepository
from src.accounts.domain.session.session import Session
from src.accounts.domain.account.value_objects.account_id import AccountId
from src.accounts.infrastructure.persistence.repositories.session import SQLBaseSessionRepository
from src.accounts.infrastructure.persistence.tables import SessionTable
from src.accounts.infrastructure.persistence.mappers.session_mapper import SessionMapper


class CachedSessionRepository(BaseSessionRepository):
    """
    Decorator pattern wrapping SQLBaseSessionRepository with a Redis cache.
    Accelerates session lookups on authenticate/refresh endpoints.
    """

    def __init__(self, database_repo: SQLBaseSessionRepository, redis_client: redis.Redis) -> None:
        self._db_repo = database_repo
        self._redis = redis_client
        self._cache_ttl_seconds = 3600  # Default fallback TTL: 1 hour

    def _get_id_key(self, session_id: str) -> str:
        return f"session:id:{session_id}"

    def _get_token_key(self, token: str) -> str:
        return f"session:token:{token}"

    def _serialize(self, session: Session) -> str:
        return json.dumps({
            "id": str(session.id.value),
            "account_id": str(session.account_id.value),
            "refresh_token": session.refresh_token.value,
            "expires_at": session.expires_at.isoformat(),
            "is_active": session.is_active,
            "is_revoked": session.is_revoked,
            "created_at": session.created_at.isoformat() if hasattr(session, "created_at") and session.created_at else None,
            "updated_at": session.updated_at.isoformat() if hasattr(session, "updated_at") and session.updated_at else None,
        })

    def _deserialize(self, data_str: str) -> Session:
        data = json.loads(data_str)
        record = SessionTable(
            id=data["id"],
            account_id=data["account_id"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            is_active=data["is_active"],
            is_revoked=data["is_revoked"],
        )
        if data.get("created_at"):
            record.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            record.updated_at = datetime.fromisoformat(data["updated_at"])
        return SessionMapper.to_domain(record)

    async def _cache_session(self, session: Session) -> None:
        now = datetime.now(timezone.utc)
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        
        ttl = int((expires - now).total_seconds())
        if ttl <= 0:
            return  # Session already expired, no need to cache

        # Limit TTL to avoid infinite/extremely long keys
        ttl = min(ttl, self._cache_ttl_seconds)

        serialized = self._serialize(session)
        id_key = self._get_id_key(str(session.id.value))
        token_key = self._get_token_key(session.refresh_token.value)

        # Pipeline write to Redis
        async with self._redis.pipeline() as pipe:
            pipe.setex(id_key, ttl, serialized)
            pipe.setex(token_key, ttl, serialized)
            await pipe.execute()

    async def _invalidate_session(self, session: Session) -> None:
        id_key = self._get_id_key(str(session.id.value))
        token_key = self._get_token_key(session.refresh_token.value)
        await self._redis.delete(id_key, token_key)

    # BaseSessionRepository implementation -------------------------------------
    async def add(self, session: Session) -> None:
        # Save in database first
        await self._db_repo.add(session)
        # Write to cache
        await self._cache_session(session)

    async def update(self, session: Session) -> None:
        # Save in database
        await self._db_repo.update(session)
        
        if not session.is_active or session.is_revoked:
            # If revoked/inactive, remove from cache immediately
            await self._invalidate_session(session)
        else:
            # Otherwise update the cache
            await self._cache_session(session)

    async def get_by_id(self, session_id: any) -> Session | None:
        id_key = self._get_id_key(str(session_id.value))
        
        # Check cache
        cached = await self._redis.get(id_key)
        if cached:
            try:
                return self._deserialize(cached.decode("utf-8"))
            except Exception:
                pass  # Fall back to database on deserialization errors

        # Cache miss, fetch from DB
        session = await self._db_repo.get_by_id(session_id)
        if session:
            await self._cache_session(session)
        return session

    async def get_by_refresh_token(self, token: any) -> Session | None:
        token_key = self._get_token_key(token.value)

        # Check cache
        cached = await self._redis.get(token_key)
        if cached:
            try:
                return self._deserialize(cached.decode("utf-8"))
            except Exception:
                pass

        # Cache miss, fetch from DB
        session = await self._db_repo.get_by_refresh_token(token)
        if session:
            await self._cache_session(session)
        return session

    async def list_for_account(self, account_id: AccountId) -> Iterable[Session]:
        # Always fetch fresh session list from the database
        return await self._db_repo.list_for_account(account_id)

    async def revoke_all_for_account(self, account_id: AccountId) -> None:
        # Revoke in DB
        await self._db_repo.revoke_all_for_account(account_id)

        # Retrieve sessions to invalidate them in Redis
        sessions = await self._db_repo.list_for_account(account_id)
        keys_to_delete = []
        for s in sessions:
            keys_to_delete.append(self._get_id_key(str(s.id.value)))
            keys_to_delete.append(self._get_token_key(s.refresh_token.value))

        if keys_to_delete:
            await self._redis.delete(*keys_to_delete)
