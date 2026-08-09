"""Shared cache-backed rate limiting primitives."""

from django.core.cache import cache


def is_rate_limited(*, key: str, max_requests: int) -> bool:
    """Return whether the current counter has reached its configured ceiling."""
    current_count = cache.get(key, 0)
    return current_count >= max_requests


def increment_rate_limit(*, key: str, window_seconds: int) -> None:
    """Increment a counter while preserving the requested expiry window."""
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window_seconds)
