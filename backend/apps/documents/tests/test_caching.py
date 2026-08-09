from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.documents.caching import (
    _CACHE_TTL_SECONDS,
    get_cached_active_document,
)
from apps.documents.models import Document
from apps.trips.models import Trip


User = get_user_model()


class DocumentCachingTests(TestCase):
    def setUp(self):
        cache.clear()

        self.user = User.objects.create_user(
            email="document-cache@example.com",
            password="Password123!",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Cache Test Trip",
            start_date="2026-08-10",
            end_date="2026-08-12",
            traveler_count=1,
        )

    def tearDown(self):
        cache.clear()
        super().tearDown()

    def test_valid_document_is_cached_after_first_lookup(self):
        document = Document.objects.create(trip=self.trip)

        with patch(
            "apps.documents.caching.get_active_document_by_token",
            wraps=lambda *, token: Document.objects.get(pk=document.pk),
        ) as selector:
            first = get_cached_active_document(token=document.share_token)
            second = get_cached_active_document(token=document.share_token)

        self.assertEqual(first.pk, document.pk)
        self.assertEqual(second.pk, document.pk)
        selector.assert_called_once_with(token=document.share_token)

    def test_invalid_token_caches_miss_sentinel(self):
        with patch(
            "apps.documents.caching.get_active_document_by_token",
            return_value=None,
        ) as selector:
            first = get_cached_active_document(token="garbage")
            second = get_cached_active_document(token="garbage")

        self.assertIsNone(first)
        self.assertIsNone(second)
        self.assertEqual(
            cache.get("documents:active_token:garbage"),
            "MISS",
        )
        selector.assert_called_once_with(token="garbage")

    def test_cache_ttl_is_shorter_than_analytics_cache(self):
        self.assertEqual(_CACHE_TTL_SECONDS, 60)

    def test_expired_document_is_cached_as_miss(self):
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        with patch(
            "apps.documents.caching.get_active_document_by_token",
            wraps=lambda *, token: None,
        ) as selector:
            result = get_cached_active_document(token=document.share_token)

        self.assertIsNone(result)
        self.assertEqual(
            cache.get(f"documents:active_token:{document.share_token}"),
            "MISS",
        )
        selector.assert_called_once_with(token=document.share_token)
