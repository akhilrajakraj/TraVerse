"""
Admin configuration for the Itinerary application.
"""

from django.contrib import admin

from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)


class ItineraryItemInline(admin.TabularInline):
    """
    Inline editor for itinerary items.
    """

    model = ItineraryItem

    extra = 0

    autocomplete_fields = (
        "destination",
    )

    ordering = (
        "order",
    )


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for itinerary days.
    """

    list_display = (
        "trip",
        "day_number",
        "date",
        "summary",
        "created_at",
    )

    list_filter = (
        "trip",
        "date",
    )

    search_fields = (
        "trip__title",
        "summary",
    )

    autocomplete_fields = (
        "trip",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "trip",
        "day_number",
    )

    inlines = (
        ItineraryItemInline,
    )


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for itinerary items.
    """

    list_display = (
        "title",
        "day",
        "destination",
        "order",
        "is_ai_generated",
        "estimated_cost_usd",
    )

    list_filter = (
        "is_ai_generated",
    )

    search_fields = (
        "title",
        "description",
    )

    autocomplete_fields = (
        "day",
        "destination",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "day",
        "order",
    )