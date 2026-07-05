from __future__ import annotations

import json

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()


class RedisCache:
    def __init__(self) -> None:
        self._client = Redis.from_url(settings.redis_url, decode_responses=True)

    async def get_json(self, key: str) -> dict | None:
        payload = await self._client.get(key)
        return json.loads(payload) if payload else None

    async def set_json(self, key: str, value: dict, ttl_seconds: int = 3600) -> None:
        await self._client.set(key, json.dumps(value), ex=ttl_seconds)
