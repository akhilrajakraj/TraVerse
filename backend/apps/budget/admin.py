"""
Django admin configuration for the Budget application.
"""

from django.contrib import admin

from apps.budget.models import (
    Budget,
    BudgetLineItem,
)


class BudgetLineItemInline(admin.TabularInline):
    """
    Inline editor for budget line items.
    """

    model = BudgetLineItem

    extra = 0

    fields = (
        "category",
        "description",
        "amount",
        "is_ai_estimated",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """
    Admin interface for Budget.
    """

    list_display = (
        "trip",
        "currency",
        "planned_total",
        "created_at",
    )

    search_fields = (
        "trip__title",
        "trip__user__email",
    )

    list_select_related = (
        "trip",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = (
        BudgetLineItemInline,
    )