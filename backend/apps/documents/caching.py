"""
Caching helpers for the Documents application.

The public share-link endpoint is a read-heavy, unpredictable traffic
hot path. Active and inactive token lookups can therefore be cached
briefly without changing the underlying selector's behavior.

A short TTL is intentional: revoking a share link should stop being
honored by a cached result within a bounded window.
"""

from __future__ import annotations

from django.core.cache import cache

from apps.documents.selectors import get_active_document_by_token


_CACHE_TTL_SECONDS = 60
_MISS_SENTINEL = "MISS"


def get_cached_active_document(*, token: str):
    """
    Return the active shared document for ``token``, using a short-lived
    cache for both successful and unsuccessful lookups.

    ``None`` is a meaningful selector result, so a string sentinel is
    used to distinguish a cached miss from an uncached key.
    """

    cache_key = f"documents:active_token:{token}"
    cached = cache.get(cache_key)

    if cached is not None:
        return None if cached == _MISS_SENTINEL else cached

    document = get_active_document_by_token(token=token)
    cache.set(
        cache_key,
        document if document is not None else _MISS_SENTINEL,
        _CACHE_TTL_SECONDS,
    )

    return document
