"""
Celery tasks for the AI Agents application.

This module provides the asynchronous entry point into the AI planning
workflow.

Responsibilities
----------------
- Receive asynchronous planning requests.
- Load the required Django models.
- Delegate execution to the AI service layer.
- Return the created AgentRun identifier.

Tasks intentionally do NOT:

- Build LangGraph state.
- Call LLM providers directly.
- Persist itinerary data.
- Contain business logic.

Those responsibilities belong to apps.ai_agents.services.
"""

from __future__ import annotations

from celery import shared_task


@shared_task(
    bind=True,
    name="apps.ai_agents.run_travel_planner",
    max_retries=0,
)
def run_travel_planner_task(
    self,
    trip_id: str,
    user_id: int | None = None,
) -> str:
    """
    Execute the Travel Planner asynchronously.

    The worker is the actual model-loading boundary for the planning
    workflow. The Trip is therefore fetched with its hot-path relations
    preloaded here rather than in the HTTP view, which only queues the
    Celery task and does not pass its Trip instance to the worker.

    Parameters
    ----------
    trip_id:
        UUID of the Trip to generate an itinerary for.

    user_id:
        Optional ID of the user who initiated the request.

    Returns
    -------
    str
        UUID of the created AgentRun.
    """

    #
    # Import lazily so Celery workers can start without importing every
    # Django model during application initialization.
    #
    from django.contrib.auth import get_user_model

    from apps.ai_agents import services
    from apps.trips.models import Trip

    #
    # Chapter 27 performance audit:
    #
    # TripPlanView queues this task using only trip_id. Any queryset
    # optimization performed in that HTTP view would be discarded before
    # the worker executes. The worker is therefore the correct caller to
    # preload the destination relation used by _build_initial_state().
    #
    trip = (
        Trip.objects
        .select_related("user")
        .prefetch_related("destinations")
        .get(pk=trip_id)
    )

    user = (
        get_user_model()
        .objects
        .filter(
            pk=user_id,
        )
        .first()
        if user_id is not None
        else None
    )

    agent_run = services.run_travel_planner(
        trip=trip,
        triggered_by=user,
    )

    return str(
        agent_run.id,
    )
