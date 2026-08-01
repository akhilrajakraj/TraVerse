"""
View tests for the Itinerary application.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.destinations.models import Destination
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.trips.models import Trip


User = get_user_model()


class ItineraryViewTests(APITestCase):
    """
    Test suite for itinerary API views.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        self.day = ItineraryDay.objects.create(
            trip=self.trip,
            date=date(2026, 4, 1),
            day_number=1,
        )

        ItineraryItem.objects.create(
            day=self.day,
            destination=self.destination,
            title="Breakfast",
            order=10,
        )

    def test_authenticated_user_can_view_itinerary(self):
        """
        Owners should retrieve their itinerary.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse(
                "itinerary:trip-itinerary",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_anonymous_user_cannot_view_itinerary(self):
        """
        Anonymous users should receive 401.
        """

        response = self.client.get(
            reverse(
                "itinerary:trip-itinerary",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_non_owner_cannot_access_itinerary(self):
        """
        Non-owners should receive 404.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            reverse(
                "itinerary:trip-itinerary",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_authenticated_user_can_add_item(self):
        """
        Owners should be able to append itinerary items.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "itinerary:add-itinerary-item",
                kwargs={
                    "day_id": self.day.id,
                },
            ),
            {
                "title": "Tokyo Tower",
                "description": "Observation deck",
                "destination_id": str(
                    self.destination.id,
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            ItineraryItem.objects.count(),
            2,
        )

    def test_non_owner_cannot_add_item(self):
        """
        Non-owners should not modify another user's itinerary.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(
            reverse(
                "itinerary:add-itinerary-item",
                kwargs={
                    "day_id": self.day.id,
                },
            ),
            {
                "title": "Museum",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )