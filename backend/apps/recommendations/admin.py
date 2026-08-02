"""
Admin configuration for the Recommendations application.
"""

from django.contrib import admin

from apps.recommendations.models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    """
    Django admin configuration for Recommendation.
    """

    list_display = (
        "destination",
        "trip",
        "category",
        "status",
        "score",
        "is_ai_generated",
        "created_at",
    )

    list_filter = (
        "category",
        "status",
        "is_ai_generated",
        "created_at",
    )

    search_fields = (
        "destination__name",
        "trip__title",
        "reason",
    )

    ordering = (
        "-score",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "trip",
        "destination",
    )