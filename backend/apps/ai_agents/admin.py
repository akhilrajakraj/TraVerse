"""
Django admin configuration for the AI Agents application.

This module registers AI execution records so administrators can monitor
travel planning requests and diagnose failures.
"""

from __future__ import annotations

from django.contrib import admin

from apps.ai_agents.models import AgentRun


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    """
    Admin interface for AI agent execution records.
    """

    list_display = (
        "id",
        "trip",
        "agent_type",
        "status",
        "triggered_by",
        "started_at",
        "completed_at",
        "created_at",
    )

    list_filter = (
        "agent_type",
        "status",
        "created_at",
    )

    search_fields = (
        "trip__title",
        "trip__user__email",
        "triggered_by__email",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "input_snapshot",
        "error_message",
    )

    autocomplete_fields = (
        "trip",
        "triggered_by",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            "Execution",
            {
                "fields": (
                    "trip",
                    "triggered_by",
                    "agent_type",
                    "status",
                ),
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "started_at",
                    "completed_at",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
        (
            "Execution Details",
            {
                "fields": (
                    "input_snapshot",
                    "error_message",
                ),
            },
        ),
    )