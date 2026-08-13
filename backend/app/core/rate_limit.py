"""Minimal in-process rate limiter.

Process-local sliding window, not shared across workers/instances. Fine for
this app's single-uvicorn-process deployment; move to a Redis-backed limiter
(e.g. slowapi + redis) before running multiple backend replicas.
"""
import time
from collections import defaultdict
from threading import Lock

_calls: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


class RateLimitExceededError(Exception):
    pass


def enforce_rate_limit(key: str, max_calls: int, window_seconds: float = 60.0) -> None:
    now = time.monotonic()
    with _lock:
        recent = [t for t in _calls[key] if now - t < window_seconds]
        if len(recent) >= max_calls:
            _calls[key] = recent
            raise RateLimitExceededError(f"Rate limit exceeded: {max_calls} requests per {window_seconds:.0f}s.")
        recent.append(now)
        _calls[key] = recent
