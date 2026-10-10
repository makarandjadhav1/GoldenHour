"""In-memory rate limiting keyed by a salted hash of the client IP (salt rotates daily; nothing persisted)."""

import hashlib
import os
import secrets
import time
from datetime import date

_salt = (date.today(), secrets.token_hex(8))
_buckets: dict[str, list[float]] = {}  # key -> [tokens, last_ts]


def _key(ip: str, kind: str) -> str:
    global _salt
    if _salt[0] != date.today():
        _salt = (date.today(), secrets.token_hex(8))
        _buckets.clear()
    return kind + hashlib.sha256((_salt[1] + ip).encode()).hexdigest()[:16]


def allow(ip: str, kind: str, per_minute: int | None = None) -> bool:
    """Token bucket: refills per_minute tokens every 60 s."""
    per_minute = per_minute or int(
        os.environ.get("RATE_LIMIT_AI" if kind == "ai" else "RATE_LIMIT_GENERAL", 10 if kind == "ai" else 60)
    )
    now, k = time.monotonic(), _key(ip, kind)
    if len(_buckets) > 20000:
        _buckets.clear()
    tokens, last = _buckets.get(k, [float(per_minute), now])
    tokens = min(per_minute, tokens + (now - last) * per_minute / 60)
    if tokens < 1:
        _buckets[k] = [tokens, now]
        return False
    _buckets[k] = [tokens - 1, now]
    return True
