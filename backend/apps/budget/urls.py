"""
URL configuration for the Budget application.
"""

from django.urls import path

from apps.budget.views import (
    BudgetLineItemCreateView,
    TripBudgetView,
)

app_name = "budget"

urlpatterns = [
    path(
        "trips/<uuid:trip_id>/budget/",
        TripBudgetView.as_view(),
        name="trip-budget",
    ),
    path(
        "trips/<uuid:trip_id>/budget/items/",
        BudgetLineItemCreateView.as_view(),
        name="budget-line-item-create",
    ),
]