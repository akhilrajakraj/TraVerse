from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.documents.models import Document
from apps.trips.models import Trip


User = get_user_model()


class DocumentIntegrationTests(TestCase):
    """
    Integration tests for the complete Documents workflow.

    These tests intentionally exercise multiple layers together:

        URL
        -> View
        -> Service
        -> Document model
        -> Selector
        -> Serializer
        -> Public API response
    """

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="owner@example.com",
            password="test-password",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test-password",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Integration Trip",
            start_date="2026-08-10",
            end_date="2026-08-12",
            traveler_count=1,
        )

    def test_create_share_link_and_access_public_itinerary(self):
        """
        A complete share-link workflow should work from the authenticated
        endpoint through the public endpoint.
        """
        self.client.force_authenticate(user=self.user)

        create_url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.trip.pk},
        )

        response = self.client.post(create_url)

        self.assertEqual(response.status_code, 201)

        document = Document.objects.get(trip=self.trip)

        self.assertTrue(document.is_active)
        self.assertTrue(document.share_token)

        self.client.force_authenticate(user=None)

        public_url = reverse(
            "public_documents:shared-itinerary",
            kwargs={"token": document.share_token},
        )

        public_response = self.client.get(public_url)

        self.assertEqual(public_response.status_code, 200)

        self.assertEqual(
            public_response.data["trip_title"],
            self.trip.title,
        )

        self.assertIn("days", public_response.data)

    def test_revoked_share_link_cannot_be_used_publicly(self):
        """
        A share link that is successfully created and then revoked must no
        longer provide access through the public endpoint.
        """
        self.client.force_authenticate(user=self.user)

        create_url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.trip.pk},
        )

        create_response = self.client.post(create_url)

        self.assertEqual(create_response.status_code, 201)

        document = Document.objects.get(trip=self.trip)

        revoke_url = reverse(
            "documents:revoke-share-link",
            kwargs={
                "pk": self.trip.pk,
                "document_id": document.pk,
            },
        )

        revoke_response = self.client.post(revoke_url)

        self.assertEqual(revoke_response.status_code, 200)

        document.refresh_from_db()

        self.assertFalse(document.is_active)

        self.client.force_authenticate(user=None)

        public_url = reverse(
            "public_documents:shared-itinerary",
            kwargs={"token": document.share_token},
        )

        public_response = self.client.get(public_url)

        self.assertEqual(public_response.status_code, 404)

    def test_expired_share_link_cannot_be_used_publicly(self):
        """
        A share link that has passed its expiration time must not be
        accessible through the public endpoint.
        """
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() - timedelta(minutes=1),
            is_active=True,
        )

        self.client.force_authenticate(user=None)

        public_url = reverse(
            "public_documents:shared-itinerary",
            kwargs={"token": document.share_token},
        )

        response = self.client.get(public_url)

        self.assertEqual(response.status_code, 404)

    def test_public_share_does_not_require_authentication(self):
        """
        A valid share token acts as the capability for public access.
        Authentication must not be required.
        """
        document = Document.objects.create(
            trip=self.trip,
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True,
        )

        self.client.force_authenticate(user=None)

        self.assertIsNone(
            self.client.handler._force_user
            if hasattr(self.client.handler, "_force_user")
            else None
        )

        public_url = reverse(
            "public_documents:shared-itinerary",
            kwargs={"token": document.share_token},
        )

        response = self.client.get(public_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["trip_title"],
            self.trip.title,
        )

    def test_user_cannot_create_share_link_for_another_users_trip(self):
        """
        Ownership must remain enforced when the complete share-link
        workflow is accessed through the API.
        """
        self.client.force_authenticate(user=self.other_user)

        create_url = reverse(
            "documents:create-share-link",
            kwargs={"pk": self.trip.pk},
        )

        response = self.client.post(create_url)

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            Document.objects.filter(trip=self.trip).exists()
        )