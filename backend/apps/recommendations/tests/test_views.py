"""View tests for the Recommendations application."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.destinations.models import Destination
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
    RecommendationStatus,
)
from apps.trips.models import Trip

User = get_user_model()


class RecommendationViewTests(APITestCase):
    """Validate Recommendation API endpoints and ownership boundaries."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
        )
        self.stranger = User.objects.create_user(
            email="stranger@example.com",
            password="password123",
        )

        self.client.force_authenticate(user=self.user)

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
        )

        self.destination = Destination.objects.create(
            name="Kyoto",
            country="Japan",
            city="Kyoto",
            latitude=Decimal("35.011600"),
            longitude=Decimal("135.768100"),
            is_active=True,
        )

        self.recommendation = Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category=RecommendationCategory.ATTRACTION,
            score=Decimal("0.95"),
            reason="Excellent cultural experience.",
        )

    def trip_url(self):
        return reverse(
            "recommendations:trip-recommendations",
            kwargs={"trip_id": self.trip.id},
        )

    def accept_url(self):
        return reverse(
            "recommendations:recommendation-accept",
            kwargs={"recommendation_id": self.recommendation.id},
        )

    def reject_url(self):
        return reverse(
            "recommendations:recommendation-reject",
            kwargs={"recommendation_id": self.recommendation.id},
        )

    def test_list_trip_recommendations(self):
        response = self.client.get(self.trip_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        self.recommendation.status = RecommendationStatus.ACCEPTED
        self.recommendation.save(update_fields=["status", "updated_at"])

        response = self.client.get(
            self.trip_url(),
            {"status": RecommendationStatus.ACCEPTED},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], RecommendationStatus.ACCEPTED)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.trip_url())

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_accept_recommendation(self):
        response = self.client.post(self.accept_url())

        self.recommendation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.recommendation.status,
            RecommendationStatus.ACCEPTED,
        )

    def test_reject_recommendation(self):
        response = self.client.post(self.reject_url())

        self.recommendation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.recommendation.status,
            RecommendationStatus.REJECTED,
        )

    def test_accept_twice_returns_400(self):
        self.client.post(self.accept_url())

        response = self.client.post(self.accept_url())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["errors"]["code"],
            "invalid_recommendation_transition",
        )

    def test_stranger_cannot_accept_recommendation(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.post(self.accept_url())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stranger_cannot_list_trip_recommendations(self):
        self.client.force_authenticate(user=self.stranger)

        response = self.client.get(self.trip_url())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_trip_not_found(self):
        response = self.client.get(
            reverse(
                "recommendations:trip-recommendations",
                kwargs={
                    "trip_id": "00000000-0000-0000-0000-000000000000",
                },
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
