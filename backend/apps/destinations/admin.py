"""
Admin configuration for the Destinations application.
"""

from django.contrib import admin

from apps.destinations.models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Destination.
    """

    list_display = (
        "name",
        "country",
        "city",
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "country",
        "city",
    )

    list_filter = (
        "country",
        "is_active",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "country",
        "city",
        "name",
    )