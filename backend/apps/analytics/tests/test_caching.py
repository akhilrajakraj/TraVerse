from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.analytics import caching


class AnalyticsCachingTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.analytics.caching.get_platform_summary")
    def test_second_platform_call_within_ttl_does_not_recompute(self, mock_get_summary):
        mock_get_summary.return_value = {
            "total_trips": 5,
            "trips_by_status": {},
            "total_agent_runs": 2,
            "agent_success_rate": 1.0,
        }

        first = caching.get_cached_platform_summary()
        second = caching.get_cached_platform_summary()

        self.assertEqual(first, second)
        mock_get_summary.assert_called_once()

    @patch("apps.analytics.caching.get_agent_performance_summary")
    def test_agent_performance_is_cached(self, mock_get_summary):
        mock_get_summary.return_value = {
            "total": 2,
            "succeeded": 2,
            "failed": 0,
            "needs_review": 0,
            "pending_or_running": 0,
        }

        caching.get_cached_agent_performance_summary()
        caching.get_cached_agent_performance_summary()

        mock_get_summary.assert_called_once()

    @patch("apps.analytics.caching.get_platform_summary", return_value={"total_trips": 1})
    def test_platform_cache_key_is_used(self, mock_get_summary):
        caching.get_cached_platform_summary()

        self.assertIsNotNone(cache.get("analytics:platform_summary"))
        mock_get_summary.assert_called_once()
