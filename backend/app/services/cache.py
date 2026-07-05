from __future__ import annotations

import json
import time


class InMemoryCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[str, float]] = {}

    async def get_json(self, key: str) -> dict | None:
        if key in self._cache:
            payload, expiry = self._cache[key]
            if expiry > time.time():
                try:
                    return json.loads(payload)
                except Exception:
                    return None
            else:
                del self._cache[key]
        return None

    async def set_json(self, key: str, value: dict, ttl_seconds: int = 3600) -> None:
        expiry = time.time() + ttl_seconds
        try:
            self._cache[key] = (json.dumps(value), expiry)
        except Exception:
            pass
