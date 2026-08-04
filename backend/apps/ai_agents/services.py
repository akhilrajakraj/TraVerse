"""
The only Django-facing entry point into the AI package.

Per the TraVerse architecture, no Django application other than
``apps.ai_agents`` may import from ``ai``.

Responsibilities
----------------
- Build the initial LangGraph state
- Execute the planning graph
- Persist validated AI output
- Record every execution attempt
"""

from __future__ import annotations

import logging

from django.utils import timezone

from decimal import Decimal

from django.db import transaction

from ai.exceptions import (
    LLMCallFailed,
    StructuredOutputInvalid,
)
from ai.graphs.planning_graph import run_planning_graph

from apps.ai_agents.models import (
    AgentRun,
    AgentRunStatus,
    AgentType,
)
from apps.itinerary import services as itinerary_services
from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip

from apps.budget import services as budget_services
from apps.budget.models import Budget

logger = logging.getLogger("apps.ai_agents")


def _build_initial_state(
    trip: Trip,
) -> dict:
    """
    Convert Django models into plain values suitable for the AI layer.

    The AI layer intentionally receives only primitive values and does
    not know anything about Django ORM models.
    """

    return {
        "trip_title": trip.title,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "destination_names": [
            destination.name
            for destination in trip.destinations.all()
        ],
        "traveler_count": trip.traveler_count,
        "trip_notes": trip.notes or "",
    }


def _persist_itinerary_plan(
    *,
    trip: Trip,
    plan,
) -> None:
    """
    Persist validated itinerary output.

    Existing AI-generated itinerary items are replaced with the newly
    generated itinerary.
    """

    for day_schema in plan.days:

        day, _ = ItineraryDay.objects.update_or_create(
            trip=trip,
            day_number=day_schema.day_number,
            defaults={
                "date": day_schema.date,
                "summary": day_schema.summary,
            },
        )

        day.items.all().delete()

        for item_schema in day_schema.items:

            itinerary_services.add_item_to_day(
                day=day,
                title=item_schema.title,
                description=item_schema.description,
                start_time=item_schema.start_time,
                estimated_cost_usd=item_schema.estimated_cost_usd,
                is_ai_generated=True,
            )

def _persist_budget_estimate(
    *,
    trip: Trip,
    budget_estimate,
) -> None:
    """
    Persist validated AI-generated budget estimates.

    Only AI-generated budget line items are replaced.
    Manual entries remain untouched.
    """

    budget, _ = Budget.objects.get_or_create(
        trip=trip,
    )

    budget.line_items.filter(
        is_ai_estimated=True,
    ).delete()

    for line_item in budget_estimate.line_items:

        budget_services.create_budget_line_item(
            budget=budget,
            category=line_item.category,
            description=line_item.description,
            amount=Decimal(
                str(line_item.estimated_amount)
            ), 
            is_ai_estimated=True,
        )

def run_travel_planner(
    *,
    trip: Trip,
    triggered_by=None,
) -> AgentRun:
    """
    Execute the complete Travel Planner workflow.
    """

    initial_state = _build_initial_state(
        trip,
    )

    agent_run = AgentRun.objects.create(
        trip=trip,
        triggered_by=triggered_by,
        agent_type=AgentType.TRAVEL_PLANNER,
        status=AgentRunStatus.RUNNING,
        input_snapshot=initial_state,
        started_at=timezone.now(),
    )

    try:

        final_state = run_planning_graph(
            initial_state,
        )
        
        with transaction.atomic():

            _persist_itinerary_plan(
                trip=trip,
                plan=final_state["itinerary"],
            )
            
            if "budget_estimate" in final_state:

                _persist_budget_estimate(
                    trip=trip,
                    budget_estimate=final_state["budget_estimate"],
                )

    except StructuredOutputInvalid as exc:

        logger.warning(
            "Travel planner needs review for trip %s: %s",
            trip.id,
            exc,
        )

        agent_run.status = AgentRunStatus.NEEDS_REVIEW
        agent_run.error_message = str(exc)

    except LLMCallFailed as exc:

        logger.error(
            "Travel planner failed for trip %s: %s",
            trip.id,
            exc,
        )

        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(exc)

    else:

        agent_run.status = AgentRunStatus.SUCCEEDED

    finally:

        agent_run.completed_at = timezone.now()

        agent_run.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
            ],
        )

    return agent_run