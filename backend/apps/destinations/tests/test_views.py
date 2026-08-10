"""
View tests for the Destinations application.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.destinations.models import Destination


User = get_user_model()


class DestinationViewTests(APITestCase):
    """
    Test suite for Destination API views.
    """

    def setUp(self):
        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            image_url="https://example.com/tokyo.jpg",
        )

        self.paris = Destination.objects.create(
            name="Paris",
            country="France",
            city="Paris",
            latitude=48.8566,
            longitude=2.3522,
        )

        self.staff_user = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            is_staff=True,
        )

        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

    def test_anonymous_user_cannot_list_destinations(self):
        response = self.client.get(reverse("destinations:destination-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_retrieve_destination(self):
        response = self.client.get(
            reverse("destinations:destination-detail", kwargs={"pk": self.destination.pk}),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_can_browse_paginated_destinations(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(reverse("destinations:destination-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_regular_user_can_search_destinations(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(
            reverse("destinations:destination-list"),
            {"search": "tok"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Tokyo")

    def test_empty_search_browses_the_catalog(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(
            reverse("destinations:destination-list"),
            {"search": ""},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_regular_user_cannot_create_destination(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.post(
            reverse("destinations:destination-list"),
            {
                "name": "Rome",
                "country": "Italy",
                "city": "Rome",
                "latitude": 41.9028,
                "longitude": 12.4964,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_create_destination(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            reverse("destinations:destination-list"),
            {
                "name": "Rome",
                "country": "Italy",
                "city": "Rome",
                "latitude": 41.9028,
                "longitude": 12.4964,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Destination.objects.count(), 3)
