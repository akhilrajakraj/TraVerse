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
from dataclasses import asdict
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ai.agents.chat_agent import ChatAgent
from ai.agents.schemas import (
    PackingListSchema,
    RecommendationBatchSchema,
    WeatherForecastSchema,
)
from ai.exceptions import LLMCallFailed, StructuredOutputInvalid
from ai.graphs.planning_graph import run_planning_graph
from ai.memory.conversation_manager import ConversationManager

from apps.ai_agents.destination_search import search_destination
from apps.ai_agents.models import AgentRun, AgentRunStatus, AgentType
from apps.budget import services as budget_services
from apps.budget.models import Budget
from apps.chat.adapters import ConversationMemoryAdapter
from apps.chat.services import ChatService
from apps.destinations.models import Destination
from apps.itinerary import services as itinerary_services
from apps.itinerary.models import ItineraryDay
from apps.notifications.models import NotificationType
from apps.recommendations import services as recommendation_services
from apps.recommendations.models import RecommendationCategory
from apps.trips import services as trip_services
from apps.trips.models import PackingCategory, Trip

logger = logging.getLogger("apps.ai_agents")


def create_notification(*, user, notification_type: str, subject: str, body: str):
    """Resolve notification creation lazily while keeping a patchable AI-service seam."""
    from apps.notifications.services import create_notification as notification_create

    return notification_create(
        user=user,
        notification_type=notification_type,
        subject=subject,
        body=body,
    )


def _build_initial_state(trip: Trip) -> dict:
    """Convert Django models into primitive values for the AI layer."""
    return {
        "trip_title": trip.title,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "destination_names": [destination.name for destination in trip.destinations.all()],
        "traveler_count": trip.traveler_count,
        "trip_notes": trip.notes or "",
    }


def _attach_conversation_context(*, session=None, state: dict, trip: Trip | None = None) -> dict:
    """Attach optimized conversation context without duplicate production lookups."""
    if session is None and trip is not None:
        session = ChatService.get_active_session(trip=trip)
    if session is None:
        return state

    memory = ConversationMemoryAdapter.build_memory(session=session)
    manager = ConversationManager()
    memory = manager.optimize_memory(memory)
    state["conversation_context"] = memory.transcript()
    return state


def _attach_destination_context(*, state: dict, user_message: str) -> dict:
    """Attach destination retrieval context to the AI state."""
    results = search_destination(query=user_message)
    if results:
        state["retrieved_destinations"] = results
    return state


def _persist_itinerary_plan(*, trip: Trip, plan) -> dict:
    """Persist validated itinerary output in batches."""
    trip = Trip.objects.select_for_update().get(pk=trip.pk)
    itinerary_days = {}

    for day_schema in plan.days:
        day = (
            ItineraryDay.objects.select_for_update()
            .filter(trip=trip, day_number=day_schema.day_number)
            .first()
        )
        if day is None:
            day = ItineraryDay.objects.create(
                trip=trip,
                day_number=day_schema.day_number,
                date=day_schema.date,
                summary=day_schema.summary,
            )
        else:
            day.date = day_schema.date
            day.summary = day_schema.summary
            day.save(update_fields=["date", "summary", "updated_at"])

        day.items.all().delete()
        items = [
            {
                "title": item_schema.title,
                "order": (index + 1) * 10,
                "description": item_schema.description,
                "start_time": item_schema.start_time,
                "estimated_cost_usd": item_schema.estimated_cost_usd,
                "is_ai_generated": True,
            }
            for index, item_schema in enumerate(day_schema.items)
        ]
        itinerary_services.add_items_to_day(day=day, items=items)
        itinerary_days[day_schema.date] = day

    return itinerary_days


def _persist_budget_estimate(*, trip: Trip, budget_estimate) -> None:
    """Persist AI-generated budget estimates as one write batch."""
    budget = Budget.objects.select_related("trip").get(trip=trip)
    line_items = [
        {
            "category": line_item.category,
            "description": line_item.description,
            "amount": Decimal(str(line_item.estimated_amount)),
        }
        for line_item in budget_estimate.line_items
    ]
    budget_services.replace_ai_estimated_line_items(budget=budget, line_items=line_items)


def _persist_weather_forecast(
    *,
    trip: Trip,
    weather_forecast: WeatherForecastSchema,
    itinerary_days: dict | None = None,
) -> None:
    """Persist weather from the planner's resolved day map."""
    if itinerary_days is None:
        dates = [weather_day.date for weather_day in weather_forecast.days]
        itinerary_days = {
            day.date: day
            for day in ItineraryDay.objects.filter(trip=trip, date__in=dates)
        }

    for weather_day in weather_forecast.days:
        itinerary_day = itinerary_days.get(weather_day.date)
        if itinerary_day is None:
            continue
        itinerary_day.weather_condition = weather_day.condition
        itinerary_day.weather_high_f = weather_day.high_f
        itinerary_day.weather_low_f = weather_day.low_f
        itinerary_day.weather_precipitation_chance = weather_day.precipitation_chance
        itinerary_day.save(
            update_fields=[
                "weather_condition",
                "weather_high_f",
                "weather_low_f",
                "weather_precipitation_chance",
            ],
        )


def _persist_recommendations(*, trip: Trip, recommendations: RecommendationBatchSchema) -> None:
    """Persist validated AI-generated recommendations."""
    recommendation_services.clear_pending_ai_recommendations(trip=trip)
    names = {recommendation.destination for recommendation in recommendations.recommendations}
    destinations = {
        destination.name: destination
        for destination in Destination.objects.filter(name__in=names)
    }
    for recommendation in recommendations.recommendations:
        destination = destinations.get(recommendation.destination)
        if destination is None:
            continue
        recommendation_services.create_recommendation(
            trip=trip,
            destination=destination,
            category=RecommendationCategory(recommendation.category),
            score=recommendation.score,
            reason=recommendation.reason,
            is_ai_generated=True,
        )


def _persist_packing_list(*, trip: Trip, packing_list: PackingListSchema) -> None:
    """Persist validated AI-generated packing items."""
    trip_services.clear_ai_generated_packing_items(trip=trip)
    for item in packing_list.items:
        trip_services.create_packing_item(
            trip=trip,
            category=PackingCategory(item.category),
            item=item.item,
            quantity=item.quantity,
            reason=item.reason,
            is_ai_generated=True,
        )


def _notify_planning_succeeded(*, trip: Trip) -> None:
    """Notify the trip owner that AI planning completed successfully."""
    create_notification(
        user=trip.user,
        notification_type=NotificationType.TRIP_PLAN_READY,
        subject=f"Your itinerary for {trip.title} is ready!",
        body=(
            f"Your AI-generated plan for {trip.title} "
            f"({trip.start_date} to {trip.end_date}) is ready to view."
        ),
    )


def run_travel_planner(*, trip: Trip, triggered_by=None) -> AgentRun:
    """Execute the complete Travel Planner workflow."""
    session = ChatService.get_active_session(trip=trip)
    initial_state = _build_initial_state(trip)
    initial_state = _attach_conversation_context(session=session, state=initial_state)
    initial_state = _attach_destination_context(
        state=initial_state,
        user_message=" ".join(initial_state["destination_names"]),
    )

    snapshot = dict(initial_state)
    if "retrieved_destinations" in snapshot:
        serialized_destinations = []
        for destination in snapshot["retrieved_destinations"]:
            data = asdict(destination)
            data["latitude"] = float(data["latitude"])
            data["longitude"] = float(data["longitude"])
            serialized_destinations.append(data)
        snapshot["retrieved_destinations"] = serialized_destinations

    agent_run = AgentRun.objects.create(
        trip=trip,
        triggered_by=triggered_by,
        agent_type=AgentType.TRAVEL_PLANNER,
        status=AgentRunStatus.RUNNING,
        input_snapshot=snapshot,
        started_at=timezone.now(),
    )

    try:
        final_state = run_planning_graph(initial_state)
        assistant_response = final_state.get("assistant_response")
        if session is not None and assistant_response:
            ChatService.add_assistant_message(session=session, content=assistant_response)

        with transaction.atomic():
            itinerary_days = _persist_itinerary_plan(trip=trip, plan=final_state["itinerary"])
            if "budget_estimate" in final_state:
                _persist_budget_estimate(trip=trip, budget_estimate=final_state["budget_estimate"])
            if "weather_forecast" in final_state:
                _persist_weather_forecast(
                    trip=trip,
                    weather_forecast=final_state["weather_forecast"],
                    itinerary_days=itinerary_days,
                )
            if "recommendations" in final_state:
                _persist_recommendations(trip=trip, recommendations=final_state["recommendations"])
            if "packing_list" in final_state:
                _persist_packing_list(trip=trip, packing_list=final_state["packing_list"])

    except StructuredOutputInvalid as exc:
        logger.warning("Travel planner needs review for trip %s: %s", trip.id, exc)
        agent_run.status = AgentRunStatus.NEEDS_REVIEW
        agent_run.error_message = str(exc)
    except LLMCallFailed as exc:
        logger.error("Travel planner failed for trip %s: %s", trip.id, exc)
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(exc)
    else:
        agent_run.status = AgentRunStatus.SUCCEEDED
        _notify_planning_succeeded(trip=trip)
    finally:
        agent_run.completed_at = timezone.now()
        agent_run.save(update_fields=["status", "error_message", "completed_at"])

    return agent_run


def generate_chat_reply(*, trip: Trip, user_message: str) -> str:
    """Execute a conversational AI request without running the planning graph."""
    session = ChatService.get_or_create_active_session(trip=trip)
    ChatService.add_user_message(session=session, content=user_message)
    memory = ConversationMemoryAdapter.build_memory(session=session)
    manager = ConversationManager()
    memory = manager.optimize_memory(memory)
    conversation_context = memory.transcript()
    retrieved_destinations = search_destination(query=user_message)
    agent = ChatAgent()
    assistant_response = agent.reply(
        conversation_context=conversation_context,
        user_message=user_message,
        retrieved_destinations=retrieved_destinations,
    ).strip()
    ChatService.add_assistant_message(session=session, content=assistant_response)
    return assistant_response
