"""
URL configuration for the AI Agents application.

This module exposes endpoints for asynchronous AI itinerary generation
and status tracking.
"""

from __future__ import annotations

from django.urls import path

from apps.ai_agents.views import (
    TripPlanStatusView,
    TripPlanView,
)

app_name = "ai_agents"

urlpatterns = [
    path(
        "trips/<uuid:trip_id>/plan/",
        TripPlanView.as_view(),
        name="trip-plan",
    ),
    path(
        "trips/<uuid:trip_id>/plan/status/",
        TripPlanStatusView.as_view(),
        name="trip-plan-status",
    ),
]