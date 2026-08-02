"""
View tests for the Budget application.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.budget.models import (
    BudgetCategory,
    BudgetLineItem,
)
from apps.trips.models import Trip


User = get_user_model()


class BudgetViewTests(APITestCase):
    """
    Test suite for Budget API views.
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
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        self.budget = self.trip.budget

        BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

    def test_authenticated_user_can_view_budget(self):
        """
        Owners should retrieve their budget.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            reverse(
                "budget:trip-budget",
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
            response.data["currency"],
            "USD",
        )

    def test_anonymous_user_cannot_view_budget(self):
        """
        Anonymous users should receive 401.
        """

        response = self.client.get(
            reverse(
                "budget:trip-budget",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_non_owner_cannot_view_budget(self):
        """
        Non-owners should receive 404.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            reverse(
                "budget:trip-budget",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_authenticated_user_can_create_budget_line_item(self):
        """
        Owners should be able to create budget line items.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.post(
            reverse(
                "budget:budget-line-item-create",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
            {
                "category": BudgetCategory.TRANSPORT,
                "description": "Metro",
                "amount": "15.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            BudgetLineItem.objects.count(),
            2,
        )

    def test_non_owner_cannot_create_budget_line_item(self):
        """
        Non-owners should not modify another user's budget.
        """

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.post(
            reverse(
                "budget:budget-line-item-create",
                kwargs={
                    "trip_id": self.trip.id,
                },
            ),
            {
                "category": BudgetCategory.FOOD,
                "description": "Dinner",
                "amount": "20.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )