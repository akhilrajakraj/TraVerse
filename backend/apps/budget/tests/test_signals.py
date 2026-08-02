"""
Signal tests for the Budget application.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget.models import (
    Budget,
    BudgetCategory,
    BudgetLineItem,
)
from apps.trips.models import Trip


User = get_user_model()


class BudgetSignalTests(TestCase):
    """
    Test suite for Budget signal handlers.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

    def test_budget_is_created_when_trip_is_created(self):
        """
        Creating a Trip should automatically create exactly
        one Budget.
        """

        trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        self.assertTrue(
            hasattr(
                trip,
                "budget",
            ),
        )

        self.assertEqual(
            Budget.objects.filter(
                trip=trip,
            ).count(),
            1,
        )

    def test_budget_total_updates_after_line_item_creation(self):
        """
        Adding a budget line item should update the Trip's
        computed budget total.
        """

        trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        BudgetLineItem.objects.create(
            budget=trip.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

        trip.refresh_from_db()

        self.assertEqual(
            trip.computed_budget_total,
            Decimal("25.00"),
        )

    def test_budget_total_updates_after_multiple_items(self):
        """
        The computed total should equal the sum of all
        budget line items.
        """

        trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        BudgetLineItem.objects.create(
            budget=trip.budget,
            category=BudgetCategory.FOOD,
            description="Breakfast",
            amount=Decimal("10.00"),
        )

        BudgetLineItem.objects.create(
            budget=trip.budget,
            category=BudgetCategory.TRANSPORT,
            description="Metro",
            amount=Decimal("15.00"),
        )

        BudgetLineItem.objects.create(
            budget=trip.budget,
            category=BudgetCategory.ACTIVITIES,
            description="Museum",
            amount=Decimal("30.00"),
        )

        trip.refresh_from_db()

        self.assertEqual(
            trip.computed_budget_total,
            Decimal("55.00"),
        )

    def test_budget_total_updates_after_line_item_deletion(self):
        """
        Removing a budget line item should immediately update
        the computed total.
        """

        trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date="2026-04-01",
            end_date="2026-04-05",
        )

        item = BudgetLineItem.objects.create(
            budget=trip.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

        item.delete()

        trip.refresh_from_db()

        self.assertEqual(
            trip.computed_budget_total,
            Decimal("0.00"),
        )