"""
Admin configuration for the Profiles application.
"""

from django.contrib import admin

from apps.profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for Profile.
    """

    list_display = (
        "user",
        "phone_number",
        "gender",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone_number",
    )

    list_filter = (
        "gender",
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )