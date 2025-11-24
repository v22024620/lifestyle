"""Simple TTL + size-bound in-memory cache for deterministic demos."""
from __future__ import annotations

import time
from typing import Any, Dict, Hashable, Optional


class TTLCache:
    """Minimal TTL cache with max size eviction (FIFO)."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 5):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._store: Dict[Hashable, tuple[float, Any]] = {}
        self._order: list[Hashable] = []

    def get(self, key: Hashable) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if now - ts > self.ttl_seconds:
            self.delete(key)
            return None
        return value

    def set(self, key: Hashable, value: Any) -> None:
        now = time.time()
        if key not in self._order:
            self._order.append(key)
        self._store[key] = (now, value)
        self._evict_if_needed()

    def delete(self, key: Hashable) -> None:
        self._store.pop(key, None)
        if key in self._order:
            self._order.remove(key)

    def _evict_if_needed(self) -> None:
        while len(self._order) > self.max_size:
            oldest = self._order.pop(0)
            self._store.pop(oldest, None)