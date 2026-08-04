"""
Models for the AI Agents application.

This app is the only Django application permitted to communicate with
the plain-Python ``ai`` package.

AgentRun records every execution attempt of an AI workflow, regardless
of whether it succeeds or fails.
"""

from django.conf import settings
from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class AgentType(models.TextChoices):
    """
    Supported AI agent types.
    """

    TRAVEL_PLANNER = (
        "travel_planner",
        "Travel Planner",
    )

    BUDGET = (
        "budget",
        "Budget",
    )

    WEATHER = (
        "weather",
        "Weather",
    )

    RECOMMENDATION = (
        "recommendation",
        "Recommendation",
    )

    PACKING = (
        "packing",
        "Packing",
    )

    FULL_GRAPH = (
        "full_graph",
        "Full Planning Graph",
    )


class AgentRunStatus(models.TextChoices):
    """
    Lifecycle states of an AI execution.
    """

    PENDING = (
        "pending",
        "Pending",
    )

    RUNNING = (
        "running",
        "Running",
    )

    SUCCEEDED = (
        "succeeded",
        "Succeeded",
    )

    FAILED = (
        "failed",
        "Failed",
    )

    NEEDS_REVIEW = (
        "needs_review",
        "Needs Review",
    )


class AgentRun(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    Records every AI execution attempt for a trip.

    This model provides a persistent audit trail for all AI runs,
    including successful executions, failures, and outputs requiring
    manual review.
    """

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )

    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="agent_runs",
    )

    agent_type = models.CharField(
        max_length=30,
        choices=AgentType.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=AgentRunStatus.choices,
        default=AgentRunStatus.PENDING,
        db_index=True,
    )

    input_snapshot = models.JSONField(
        default=dict,
        help_text=(
            "The exact graph state used as input. "
            "Stored for reproducibility and debugging."
        ),
    )

    error_message = models.TextField(
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "trip",
                    "agent_type",
                    "created_at",
                ],
            ),
        ]

        verbose_name = "Agent Run"

        verbose_name_plural = "Agent Runs"

    def __str__(self) -> str:
        return (
            f"{self.agent_type} "
            f"run for "
            f"{self.trip.title} "
            f"({self.status})"
        )