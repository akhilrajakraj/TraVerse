"""
Selector tests for the Budget application.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget.models import (
    BudgetCategory,
    BudgetLineItem,
)
from apps.budget.selectors import calculate_budget_total
from apps.trips.models import Trip


User = get_user_model()


class BudgetSelectorTests(TestCase):
    """
    Test suite for Budget selectors.
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

    def test_empty_budget_returns_zero(self):
        """
        Budgets without line items should total 0.00.
        """

        total = calculate_budget_total(
            self.budget,
        )

        self.assertEqual(
            total,
            Decimal("0.00"),
        )

    def test_single_line_item_total(self):
        """
        A single line item should equal the budget total.
        """

        BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

        total = calculate_budget_total(
            self.budget,
        )

        self.assertEqual(
            total,
            Decimal("25.00"),
        )

    def test_multiple_line_items_total(self):
        """
        Multiple line items should be summed correctly.
        """

        BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Breakfast",
            amount=Decimal("10.00"),
        )

        BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.TRANSPORT,
            description="Metro",
            amount=Decimal("15.00"),
        )

        BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.ACTIVITIES,
            description="Museum",
            amount=Decimal("30.00"),
        )

        total = calculate_budget_total(
            self.budget,
        )

        self.assertEqual(
            total,
            Decimal("55.00"),
        )

    def test_selector_returns_decimal(self):
        """
        Selector should always return a Decimal.
        """

        total = calculate_budget_total(
            self.budget,
        )

        self.assertIsInstance(
            total,
            Decimal,
        )