"""
Model tests for the Budget application.
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


class BudgetModelTests(TestCase):
    """
    Test suite for Budget domain models.
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

    def test_budget_created_for_trip(self):
        """
        Every Trip should own exactly one Budget.
        """

        self.assertIsInstance(
            self.budget,
            Budget,
        )

        self.assertEqual(
            self.budget.trip,
            self.trip,
        )

    def test_create_budget_line_item(self):
        """
        Budget line items should be created successfully.
        """

        item = BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.50"),
        )

        self.assertEqual(
            item.budget,
            self.budget,
        )

        self.assertEqual(
            item.amount,
            Decimal("25.50"),
        )

    def test_budget_string_representation(self):
        """
        Budget.__str__ should be informative.
        """

        self.assertEqual(
            str(self.budget),
            f"Budget<{self.trip.title}>",
        )

    def test_budget_line_item_string_representation(self):
        """
        BudgetLineItem.__str__ should include description,
        amount, and category.
        """

        item = BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.TRANSPORT,
            description="Metro",
            amount=Decimal("8.00"),
        )

        self.assertEqual(
            str(item),
            "Metro: 8.00 (transport)",
        )

    def test_budget_line_items_are_ordered_by_created_at_desc(self):
        """
        Newest line items should appear first.
        """

        older = BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Breakfast",
            amount=Decimal("10.00"),
        )

        newer = BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Dinner",
            amount=Decimal("30.00"),
        )

        items = list(
            BudgetLineItem.objects.all(),
        )

        self.assertEqual(
            items[0],
            newer,
        )

        self.assertEqual(
            items[1],
            older,
        )

    def test_budget_has_one_to_one_relationship_with_trip(self):
        """
        Budget should maintain a one-to-one relationship
        with Trip.
        """

        self.assertEqual(
            Budget.objects.count(),
            1,
        )

        self.assertEqual(
            self.trip.budget.id,
            self.budget.id,
        )