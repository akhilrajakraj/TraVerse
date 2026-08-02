"""
Serializer tests for the Budget application.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget.models import (
    BudgetCategory,
    BudgetLineItem,
)
from apps.budget.serializers import (
    BudgetLineItemSerializer,
    BudgetSerializer,
    CreateBudgetLineItemSerializer,
)
from apps.trips.models import Trip


User = get_user_model()


class BudgetSerializerTests(TestCase):
    """
    Test suite for Budget serializers.
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

        self.item = BudgetLineItem.objects.create(
            budget=self.budget,
            category=BudgetCategory.FOOD,
            description="Lunch",
            amount=Decimal("25.00"),
        )

        self.trip.refresh_from_db()

    def test_budget_line_item_serializer(self):
        """
        BudgetLineItemSerializer should serialize fields correctly.
        """

        serializer = BudgetLineItemSerializer(
            self.item,
        )

        self.assertEqual(
            serializer.data["description"],
            "Lunch",
        )

        self.assertEqual(
            serializer.data["category"],
            BudgetCategory.FOOD,
        )

        self.assertEqual(
            serializer.data["amount"],
            "25.00",
        )

    def test_budget_serializer(self):
        """
        BudgetSerializer should include nested line items
        and computed total.
        """

        serializer = BudgetSerializer(
            self.budget,
        )

        self.assertEqual(
            serializer.data["currency"],
            "USD",
        )

        self.assertEqual(
            serializer.data["computed_total"],
            "25.00",
        )

        self.assertEqual(
            len(
                serializer.data["line_items"],
            ),
            1,
        )

    def test_create_budget_line_item_serializer_valid(self):
        """
        Valid payloads should pass validation.
        """

        serializer = CreateBudgetLineItemSerializer(
            data={
                "category": BudgetCategory.TRANSPORT,
                "description": "Metro",
                "amount": "15.00",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
        )

    def test_create_budget_line_item_serializer_invalid_category(self):
        """
        Invalid categories should fail validation.
        """

        serializer = CreateBudgetLineItemSerializer(
            data={
                "category": "invalid-category",
                "description": "Metro",
                "amount": "15.00",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )