"""
Business services for the Budget application.
"""

from decimal import Decimal

from apps.budget.models import (
    Budget,
    BudgetCategory,
    BudgetLineItem,
)


def create_budget_line_item(
    *,
    budget: Budget,
    category: BudgetCategory | str,
    description: str,
    amount: Decimal,
    is_ai_estimated: bool = False,
) -> BudgetLineItem:
    """
    Create a new budget line item.

    Updating the trip's computed budget total is handled
    automatically by the application's signal handlers.
    """

    return BudgetLineItem.objects.create(
        budget=budget,
        category=category,
        description=description,
        amount=amount,
        is_ai_estimated=is_ai_estimated,
    )