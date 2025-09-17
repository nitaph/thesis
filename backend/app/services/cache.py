# app/services/cache.py
from __future__ import annotations

import time
from typing import Optional

# Try Redis (async); fall back to in-memory cache if not available or URL is missing
try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class InMemoryCache:
    """
    Simple in-process cache with TTL.
    Stores key -> (expires_at_epoch_seconds | None, value_str).
    """
    def __init__(self) -> None:
        self._data: dict[str, tuple[Optional[float], str]] = {}

    async def get(self, key: str) -> Optional[str]:
        item = self._data.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at is not None and time.time() >= expires_at:
            # expired: remove and miss
            self._data.pop(key, None)
            return None
        return value

    async def setex(self, key: str, ttl: int, value: str) -> None:
        expires_at = (time.time() + ttl) if ttl and ttl > 0 else None
        self._data[key] = (expires_at, value)

    def clear(self) -> None:
        self._data.clear()

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class Cache:
    """
    Unified cache wrapper used by services.
    - If REDIS_URL is provided and redis.asyncio is installed, uses Redis.
    - Otherwise uses an in-memory TTL cache (per-process, non-shared).
    """
    def __init__(self, url: Optional[str], ttl_s: int) -> None:
        self.ttl = ttl_s
        self._is_redis = bool(url and redis is not None)
        if self._is_redis:
            # decode_responses=True -> str in/out
            self.client = redis.from_url(url, encoding="utf-8", decode_responses=True)  # type: ignore
        else:
            self.client = InMemoryCache()

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: str) -> None:
        # Prefer setex; fall back to set(ex=...) if needed
        if self._is_redis:
            try:
                await self.client.setex(key, self.ttl, value)  # type: ignore[attr-defined]
            except AttributeError:
                await self.client.set(key, value, ex=self.ttl)  # type: ignore[attr-defined]
        else:
            await self.client.setex(key, self.ttl, value)

    async def delete(self, key: str) -> None:
        if self._is_redis:
            await self.client.delete(key)  # type: ignore[attr-defined]
        else:
            self.client.delete(key)

    async def clear(self) -> None:
        if self._is_redis:
            # Clears only the selected Redis DB
            await self.client.flushdb()  # type: ignore[attr-defined]
        else:
            self.client.clear()

    @staticmethod
    def make_key(participant_id: str, task_id: str, condition: str) -> str:
        return f"resp:{participant_id}:{task_id}:{condition}"
