"""
Read-side selectors for the Budget application.
"""

from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.budget.models import Budget


def calculate_budget_total(
    budget: Budget,
) -> Decimal:
    """
    Calculate the total amount of all line items belonging
    to a budget.

    Returns Decimal('0.00') when the budget contains no
    line items.
    """

    return budget.line_items.aggregate(
        total_amount=Coalesce(
            Sum(
                "amount",
            ),
            Decimal("0.00"),
        ),
    )["total_amount"]