from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.documents.models import Document
from apps.documents.services import (
    create_share_link,
    generate_itinerary_pdf,
    revoke_share_link,
)
from apps.trips.models import Trip


User = get_user_model()


class DocumentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="documents@example.com",
            password="Password123!",
            first_name="Documents",
            last_name="Tester",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Test Trip",
            start_date="2026-08-10",
            end_date="2026-08-12",
            traveler_count=1,
        )

    def test_create_share_link(self):
        expires_at = timezone.now() + timedelta(days=7)

        document = create_share_link(
            trip=self.trip,
            expires_at=expires_at,
        )

        self.assertEqual(
            document.trip,
            self.trip,
        )

        self.assertTrue(
            document.is_active,
        )

        self.assertEqual(
            document.expires_at,
            expires_at,
        )

        self.assertTrue(
            document.share_token,
        )

        self.assertEqual(
            len(document.share_token),
            43,
        )

    def test_revoke_share_link(self):
        document = create_share_link(
            trip=self.trip,
        )

        result = revoke_share_link(
            document=document,
        )

        self.assertEqual(
            result.pk,
            document.pk,
        )

        self.assertFalse(
            result.is_active,
        )

        document.refresh_from_db()

        self.assertFalse(
            document.is_active,
        )

    @patch("apps.documents.services.get_trip_itinerary")
    @patch("apps.documents.services.ItineraryDaySerializer")
    def test_generate_itinerary_pdf(
        self,
        mock_serializer,
        mock_get_itinerary,
    ):
        mock_get_itinerary.return_value = []

        mock_serializer.return_value.data = []

        response = generate_itinerary_pdf(
            trip=self.trip,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertIn(
            "attachment",
            response["Content-Disposition"],
        )

        self.assertIn(
            "Test Trip-itinerary.pdf",
            response["Content-Disposition"],
        )

        content = b"".join(
            response.streaming_content,
        )

        self.assertTrue(
            content.startswith(b"%PDF"),
        )