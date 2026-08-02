"""
Serializers for the Budget application.
"""

from rest_framework import serializers

from apps.budget.models import (
    Budget,
    BudgetLineItem,
)


class BudgetLineItemSerializer(serializers.ModelSerializer):
    """
    Read serializer for budget line items.
    """

    class Meta:
        model = BudgetLineItem

        fields = [
            "id",
            "category",
            "description",
            "amount",
            "is_ai_estimated",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "is_ai_estimated",
        ]


class BudgetSerializer(serializers.ModelSerializer):
    """
    Read serializer for budgets.
    """

    line_items = BudgetLineItemSerializer(
        many=True,
        read_only=True,
    )

    computed_total = serializers.DecimalField(
        source="trip.computed_budget_total",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Budget

        fields = [
            "id",
            "currency",
            "planned_total",
            "computed_total",
            "line_items",
        ]

        read_only_fields = [
            "id",
            "computed_total",
            "line_items",
        ]


class CreateBudgetLineItemSerializer(serializers.Serializer):
    """
    Serializer used when creating a budget line item.
    """

    category = serializers.ChoiceField(
        choices=BudgetLineItem._meta.get_field(
            "category",
        ).choices,
    )

    description = serializers.CharField(
        max_length=200,
    )

    amount = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    is_ai_estimated = serializers.BooleanField(
        required=False,
        default=False,
    )