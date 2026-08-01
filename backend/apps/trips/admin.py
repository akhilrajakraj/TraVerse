"""
Admin configuration for the Trips application.
"""

from django.contrib import admin

from apps.trips.models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """
    Administrative configuration for Trip objects.
    """

    list_display = (
        "title",
        "user",
        "status",
        "traveler_count",
        "start_date",
        "end_date",
        "created_at",
    )

    search_fields = (
        "title",
        "user__email",
    )

    list_filter = (
        "status",
        "start_date",
        "end_date",
        "created_at",
    )

    readonly_fields = (
        "id",
        "computed_budget_total",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "user",
        "destinations",
    )

    filter_horizontal = (
        "destinations",
    )

    ordering = (
        "-created_at",
    )