from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.documents.models import Document
from apps.documents.selectors import get_active_document_by_token
from apps.trips.models import Trip


User = get_user_model()


class DocumentSelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="selector@example.com",
            password="Password123!",
            first_name="Selector",
            last_name="Tester",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Selector Test Trip",
            start_date="2026-08-10",
            end_date="2026-08-12",
            traveler_count=1,
        )

    def test_returns_active_document_by_token(self):
        document = Document.objects.create(
            trip=self.trip,
        )

        result = get_active_document_by_token(
            token=document.share_token,
        )

        self.assertEqual(
            result,
            document,
        )

    def test_returns_none_for_unknown_token(self):
        result = get_active_document_by_token(
            token="nonexistent-token",
        )

        self.assertIsNone(result)

    def test_returns_none_for_revoked_document(self):
        document = Document.objects.create(
            trip=self.trip,
            is_active=False,
        )

        result = get_active_document_by_token(
            token=document.share_token,
        )

        self.assertIsNone(result)

    def test_returns_none_for_expired_document(self):
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        result = get_active_document_by_token(
            token=document.share_token,
        )

        self.assertIsNone(result)

    def test_returns_document_for_non_expired_document(self):
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() + timedelta(days=1),
        )

        result = get_active_document_by_token(
            token=document.share_token,
        )

        self.assertEqual(
            result,
            document,
        )