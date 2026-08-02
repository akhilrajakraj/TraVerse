"""
Signal handlers for the Budget application.
"""

from django.db.models.signals import (
    post_delete,
    post_save,
)
from django.dispatch import receiver

from apps.budget.models import (
    Budget,
    BudgetLineItem,
)
from apps.budget.selectors import calculate_budget_total
from apps.trips.models import Trip


@receiver(
    post_save,
    sender=Trip,
)
def create_budget_for_trip(
    sender,
    instance: Trip,
    created: bool,
    **kwargs,
) -> None:
    """
    Automatically create a Budget whenever a new Trip
    is created.
    """

    if not created:
        return

    Budget.objects.create(
        trip=instance,
    )


@receiver(
    post_save,
    sender=BudgetLineItem,
)
@receiver(
    post_delete,
    sender=BudgetLineItem,
)
def synchronize_trip_budget_total(
    sender,
    instance: BudgetLineItem,
    **kwargs,
) -> None:
    """
    Synchronize Trip.computed_budget_total whenever
    budget line items change.
    """

    budget = instance.budget

    trip = budget.trip

    trip.computed_budget_total = calculate_budget_total(
        budget=budget,
    )

    trip.save(
        update_fields=[
            "computed_budget_total",
        ],
    )