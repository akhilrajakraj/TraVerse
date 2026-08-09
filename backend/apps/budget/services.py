"""
Business services for the Budget application.
"""

from decimal import Decimal

from apps.budget.models import (
    Budget,
    BudgetCategory,
    BudgetLineItem,
)
from apps.budget.selectors import calculate_budget_total


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


def replace_ai_estimated_line_items(
    *,
    budget: Budget,
    line_items: list[dict],
) -> None:
    """
    Replace AI-estimated budget line items in one write batch.

    The normal single-item creation service intentionally keeps its
    signal-driven behavior. The planner, however, replaces an entire
    generated batch inside its own transaction. Using ``bulk_create``
    avoids running the budget-total signal once per generated item, so the
    total is recalculated exactly once after the batch is written.
    """

    budget.line_items.filter(
        is_ai_estimated=True,
    ).delete()

    BudgetLineItem.objects.bulk_create(
        [
            BudgetLineItem(
                budget=budget,
                category=item["category"],
                description=item["description"],
                amount=item["amount"],
                is_ai_estimated=True,
            )
            for item in line_items
        ]
    )

    budget.trip.computed_budget_total = calculate_budget_total(
        budget=budget,
    )
    budget.trip.save(
        update_fields=[
            "computed_budget_total",
        ],
    )
