"""
Service tests for the Budget application.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget.models import (
    BudgetCategory,
)
from apps.budget.services import create_budget_line_item
from apps.trips.models import Trip


User = get_user_model()


class BudgetServiceTests(TestCase):
    """
    Test suite for Budget services.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        self.budget = self.trip.budget

    def test_create_budget_line_item(self):
        """
        Service should create a budget line item.
        """

        item = create_budget_line_item(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

        self.assertEqual(
            item.budget,
            self.budget,
        )

        self.assertEqual(
            item.description,
            "Lunch",
        )

        self.assertEqual(
            item.amount,
            Decimal("25.00"),
        )

        self.assertFalse(
            item.is_ai_estimated,
        )

    def test_create_ai_estimated_budget_line_item(self):
        """
        Service should allow AI-generated estimates.
        """

        item = create_budget_line_item(
            budget=self.budget,
            category=BudgetCategory.ACTIVITIES,
            description="AI Suggested Tour",
            amount=Decimal("150.00"),
            is_ai_estimated=True,
        )

        self.assertTrue(
            item.is_ai_estimated,
        )

    def test_service_updates_trip_budget_total_via_signal(self):
        """
        Creating a line item through the service should
        result in the Trip total being synchronized by
        the signal layer.
        """

        create_budget_line_item(
            budget=self.budget,
            category=BudgetCategory.TRANSPORT,
            description="Metro",
            amount=Decimal("20.00"),
        )

        self.trip.refresh_from_db()

        self.assertEqual(
            self.trip.computed_budget_total,
            Decimal("20.00"),
        )

    def test_multiple_service_calls_accumulate_budget_total(self):
        """
        Multiple service calls should accumulate the
        computed budget total correctly.
        """

        create_budget_line_item(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Breakfast",
            amount=Decimal("10.00"),
        )

        create_budget_line_item(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Dinner",
            amount=Decimal("30.00"),
        )

        self.trip.refresh_from_db()

        self.assertEqual(
            self.trip.computed_budget_total,
            Decimal("40.00"),
        )