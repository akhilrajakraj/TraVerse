"""
View tests for the Trips application.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.trips.models import (
    Trip,
    TripStatus,
    PackingItem,
    PackingCategory,
)

User = get_user_model()


class TripViewTests(APITestCase):
    """
    Test suite for Trip API views.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="traveler@example.com",
            password="Password123!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Vacation",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
        )

    def test_authenticated_user_can_list_own_trips(self):
        """
        Authenticated users should only see their own trips.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse(
                "trips:trip-list",
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

    def test_authenticated_user_can_create_trip(self):
        """
        Authenticated users should create trips.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "trips:trip-list",
            ),
            {
                "title": "Europe Trip",
                "start_date": str(date.today()),
                "end_date": str(
                    date.today() + timedelta(days=6),
                ),
                "traveler_count": 2,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Trip.objects.count(),
            2,
        )

    def test_user_cannot_access_other_users_trip(self):
        """
        Users must not retrieve another user's trip.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            reverse(
                "trips:trip-detail",
                kwargs={
                    "pk": self.trip.pk,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_valid_status_transition(self):
        """
        Valid lifecycle transitions should succeed.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "trips:trip-status",
                kwargs={
                    "pk": self.trip.pk,
                },
            ),
            {
                "status": TripStatus.PLANNING,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.trip.refresh_from_db()

        self.assertEqual(
            self.trip.status,
            TripStatus.PLANNING,
        )

    def test_invalid_status_transition(self):
        """
        Invalid lifecycle transitions should fail.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "trips:trip-status",
                kwargs={
                    "pk": self.trip.pk,
                },
            ),
            {
                "status": TripStatus.COMPLETED,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        
class TripPackingListViewTests(APITestCase):
    """
    Test suite for TripPackingListView.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="traveler@example.com",
            password="Password123!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Vacation",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
        )

        PackingItem.objects.create(
            trip=self.trip,
            category=PackingCategory.CLOTHING,
            item="Rain Jacket",
            quantity=1,
            reason="Expected rain.",
        )

        self.url = reverse(
            "trips:trip-packing-list",
            kwargs={
                "pk": self.trip.pk,
            },
        )

    def test_owner_receives_packing_list(self):
        """
        The trip owner should receive the generated packing list.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["item"],
            "Rain Jacket",
        )

    def test_other_user_receives_404(self):
        """
        Users should not access another user's packing list.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_unauthenticated_request(self):
        """
        Authentication is required.
        """

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_empty_packing_list(self):
        """
        Trips without packing items should return an empty list.
        """

        PackingItem.objects.all().delete()

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.url,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data,
            [],
        )