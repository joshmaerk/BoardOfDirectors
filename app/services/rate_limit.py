"""User-aware token bucket for per-route rate limiting.

slowapi's `Limiter.limit` decorator runs before FastAPI dependency
resolution, so it cannot key on the authenticated `oid`. This module
provides a simple in-process token bucket keyed by (user_oid, route)
that is invoked from inside the route after the user is known.

Production deployments with multiple API replicas should plug in a
Redis-backed bucket here; the protocol is intentionally small.
"""

from __future__ import annotations

import re
import threading
import time
from collections import deque
from typing import Protocol


class RateLimiter(Protocol):
    def check(self, key: str, limit_spec: str) -> bool:
        """Return True if the call should be allowed, False if rejected."""
        ...


_LIMIT_RE = re.compile(r"^\s*(\d+)\s*/\s*(second|minute|hour|day)\s*$", re.IGNORECASE)

_WINDOW_SECONDS = {"second": 1, "minute": 60, "hour": 3600, "day": 86_400}


def _parse_limit(spec: str) -> tuple[int, int]:
    """`30/hour` -> (count=30, window_seconds=3600)."""
    match = _LIMIT_RE.match(spec)
    if not match:
        raise ValueError(f"Invalid rate-limit spec: {spec!r}")
    count = int(match.group(1))
    window = _WINDOW_SECONDS[match.group(2).lower()]
    return count, window


class InMemoryRateLimiter:
    """Sliding-window token bucket, thread-safe, per-process."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str, limit_spec: str) -> bool:
        count, window = _parse_limit(limit_spec)
        now = time.monotonic()
        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            cutoff = now - window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= count:
                return False
            bucket.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


_default = InMemoryRateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _default


def reset_default_for_tests() -> None:
    _default.clear()
