from django.http import HttpResponse

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Document
from apps.trips.models import Trip


User = get_user_model()


class DocumentViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="documents-view@example.com",
            password="Password123!",
            first_name="Documents",
            last_name="Viewer",
        )

        self.other_user = User.objects.create_user(
            email="documents-other@example.com",
            password="Password123!",
            first_name="Other",
            last_name="Viewer",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="View Test Trip",
            start_date="2026-08-10",
            end_date="2026-08-12",
            traveler_count=1,
        )

        self.other_trip = Trip.objects.create(
            user=self.other_user,
            title="Other User Trip",
            start_date="2026-08-15",
            end_date="2026-08-17",
            traveler_count=1,
        )

    def test_create_share_link_requires_authentication(self):
        url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.trip.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_create_share_link_for_owned_trip(self):
        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.trip.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["id"],
            str(Document.objects.get(trip=self.trip).id),
        )

        self.assertIn(
            "share_url",
            response.data,
        )

        self.assertTrue(
            response.data["is_active"],
        )

    def test_create_share_link_cannot_access_other_users_trip(self):
        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.other_trip.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_revoke_share_link_for_owned_trip(self):
        document = Document.objects.create(
            trip=self.trip,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "documents:revoke-share-link",
            kwargs={
                "pk": self.trip.pk,
                "document_id": document.pk,
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        document.refresh_from_db()

        self.assertFalse(
            document.is_active,
        )

    def test_revoke_share_link_cannot_revoke_other_users_document(self):
        document = Document.objects.create(
            trip=self.other_trip,
        )

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "documents:revoke-share-link",
            kwargs={
                "pk": self.other_trip.pk,
                "document_id": document.pk,
            },
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        document.refresh_from_db()

        self.assertTrue(
            document.is_active,
        )

    @patch("apps.documents.views.services.generate_itinerary_pdf")
    def test_generate_itinerary_pdf_for_owned_trip(
        self,
        mock_generate_pdf,
    ):
        self.client.force_authenticate(
            user=self.user,
        )

        pdf_response = HttpResponse(
            b"%PDF-test",
            content_type="application/pdf",
        )

        mock_generate_pdf.return_value = pdf_response

        url = reverse(
            "documents:trip-pdf",
            kwargs={"pk": self.trip.pk},
        )

        response = self.client.get(url)

        mock_generate_pdf.assert_called_once_with(
            trip=self.trip,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertTrue(
            response.content.startswith(b"%PDF"),
        )

    def test_generate_itinerary_pdf_cannot_access_other_users_trip(self):
        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "documents:trip-pdf",
            kwargs={"pk": self.other_trip.pk},
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch("apps.documents.views.get_trip_itinerary")
    def test_public_share_returns_itinerary(
        self,
        mock_get_trip_itinerary,
    ):
        document = Document.objects.create(
            trip=self.trip,
        )

        mock_get_trip_itinerary.return_value = []

        url = reverse(
            "public_documents:shared-itinerary",
            kwargs={
                "token": document.share_token,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["trip_title"],
            self.trip.title,
        )

        self.assertEqual(
            str(response.data["start_date"]),
            str(self.trip.start_date),
        )

        self.assertEqual(
            str(response.data["end_date"]),
            str(self.trip.end_date),
        )

        self.assertEqual(
            response.data["days"],
            [],
        )

        mock_get_trip_itinerary.assert_called_once_with(
            trip=self.trip,
        )

    def test_public_share_returns_404_for_unknown_token(self):
        url = reverse(
            "public_documents:shared-itinerary",
            kwargs={
                "token": "does-not-exist",
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_public_share_returns_404_for_revoked_document(self):
        document = Document.objects.create(
            trip=self.trip,
            is_active=False,
        )

        url = reverse(
            "public_documents:shared-itinerary",
            kwargs={
                "token": document.share_token,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_public_share_returns_404_for_expired_document(self):
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        url = reverse(
            "public_documents:shared-itinerary",
            kwargs={
                "token": document.share_token,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )