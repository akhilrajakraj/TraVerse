"""
Serializers for the AI Agents application.

This module exposes read-only serializers used by the AI planning API.

The serializer intentionally exposes only the information required by
clients polling the status of an AI planning request.

Write operations are performed through Celery tasks and the service
layer, never through DRF serializers.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.ai_agents.models import AgentRun


class AgentRunStatusSerializer(serializers.ModelSerializer):
    """
    Read-only representation of an AI agent execution.

    Used by the status endpoint to report the latest planning run for
    a trip.
    """

    class Meta:
        model = AgentRun

        fields = (
            "id",
            "agent_type",
            "status",
            "error_message",
            "started_at",
            "completed_at",
        )

        read_only_fields = fields