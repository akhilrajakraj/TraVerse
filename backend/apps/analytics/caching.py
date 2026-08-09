"""
Cached analytics accessors.

Analytics uses cache.get_or_set() because aggregate calculations are
expensive enough to cache briefly and do not need second-level freshness.
"""

from django.core.cache import cache

from apps.analytics.selectors import (
    get_agent_performance_summary,
    get_booking_intent_summary,
    get_platform_summary,
    get_recommendation_acceptance_rate,
)

_CACHE_TTL_SECONDS = 300


def get_cached_platform_summary() -> dict:
    return cache.get_or_set(
        "analytics:platform_summary",
        get_platform_summary,
        _CACHE_TTL_SECONDS,
    )


def get_cached_agent_performance_summary() -> dict:
    return cache.get_or_set(
        "analytics:agent_performance",
        get_agent_performance_summary,
        _CACHE_TTL_SECONDS,
    )


def get_cached_recommendation_acceptance_rate() -> float:
    return cache.get_or_set(
        "analytics:recommendation_acceptance",
        get_recommendation_acceptance_rate,
        _CACHE_TTL_SECONDS,
    )


def get_cached_booking_intent_summary() -> dict:
    return cache.get_or_set(
        "analytics:booking_intent_summary",
        get_booking_intent_summary,
        _CACHE_TTL_SECONDS,
    )
