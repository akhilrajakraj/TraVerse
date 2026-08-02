"""
View tests for the Recommendations application.
"""

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
    """
    Validate Recommendation API endpoints.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
        )

        self.client.force_authenticate(
            user=self.user,
        )

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

    def test_list_trip_recommendations(self):
        url = reverse(
            "recommendations:trip-recommendations",
            kwargs={
                "trip_id": self.trip.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        url = reverse(
            "recommendations:trip-recommendations",
            kwargs={
                "trip_id": self.trip.id,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_accept_recommendation(self):
        url = reverse(
            "recommendations:recommendation-accept",
            kwargs={
                "recommendation_id": self.recommendation.id,
            },
        )

        response = self.client.post(url)

        self.recommendation.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.recommendation.status,
            RecommendationStatus.ACCEPTED,
        )

    def test_reject_recommendation(self):
        url = reverse(
            "recommendations:recommendation-reject",
            kwargs={
                "recommendation_id": self.recommendation.id,
            },
        )

        response = self.client.post(url)

        self.recommendation.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            self.recommendation.status,
            RecommendationStatus.REJECTED,
        )

    def test_trip_not_found(self):
        url = reverse(
            "recommendations:trip-recommendations",
            kwargs={
                "trip_id": "00000000-0000-0000-0000-000000000000",
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )