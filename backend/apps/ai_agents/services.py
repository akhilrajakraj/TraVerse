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
from requests import session

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

from ai.agents.schemas import (
    RecommendationBatchSchema,
    WeatherForecastSchema,
    PackingListSchema,
)

from apps.budget import services as budget_services
from apps.budget.models import Budget

from apps.recommendations import services as recommendation_services
from apps.recommendations.models import RecommendationCategory

from apps.destinations.models import Destination

from apps.trips import services as trip_services
from apps.trips.models import (
    PackingCategory,
    Trip,
)

from ai.memory.conversation_manager import ConversationManager

from apps.chat.adapters import ConversationMemoryAdapter
from apps.chat.services import ChatService

from ai.agents.chat_agent import ChatAgent
from apps.chat.models import ChatSession

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
    
def _attach_conversation_context(
    *,
    trip: Trip,
    state: dict,
) -> dict:
    
    session = ChatService.get_active_session(
        trip=trip,
    )
    
    if session is None:
        return state
    
    memory = ConversationMemoryAdapter.build_memory(
        session=session,
    )
    
    manager = ConversationManager()
    
    memory = manager.optimize_memory(
        memory,
    )
    
    state["conversation_context"] = (
        memory.transcript()
    )
    
    return state


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

def _persist_weather_forecast(
    *,
    trip: Trip,
    weather_forecast: WeatherForecastSchema,
) -> None:
    """
    Persist validated AI-generated weather forecasts.

    Weather is attached to existing itinerary days.

    Only weather-related fields are updated.
    """

    for weather_day in weather_forecast.days:

        try:
            itinerary_day = ItineraryDay.objects.get(
                trip=trip,
                date=weather_day.date,
            )

        except ItineraryDay.DoesNotExist:
            #
            # Skip weather for itinerary days that do not exist.
            #
            continue

        itinerary_day.weather_condition = (
            weather_day.condition
        )

        itinerary_day.weather_high_f = (
            weather_day.high_f
        )

        itinerary_day.weather_low_f = (
            weather_day.low_f
        )

        itinerary_day.weather_precipitation_chance = (
            weather_day.precipitation_chance
        )

        itinerary_day.save(
            update_fields=[
                "weather_condition",
                "weather_high_f",
                "weather_low_f",
                "weather_precipitation_chance",
            ],
        )
        
def _persist_recommendations(
    *,
    trip: Trip,
    recommendations: RecommendationBatchSchema,
) -> None:
    """
    Persist validated AI-generated recommendations.

    Existing pending AI recommendations are replaced while preserving
    recommendations that have already been accepted or rejected by the
    user.
    """

    recommendation_services.clear_pending_ai_recommendations(
        trip=trip,
    )

    for recommendation in recommendations.recommendations:

        destination = Destination.objects.filter(
            name=recommendation.destination,
        ).first()

        #
        # Ignore recommendations whose destination cannot be resolved.
        #
        if destination is None:
            continue

        recommendation_services.create_recommendation(
            trip=trip,
            destination=destination,
            category=RecommendationCategory(
                recommendation.category,
            ),
            score=recommendation.score,
            reason=recommendation.reason,
            is_ai_generated=True,
        )

def _persist_packing_list(
    *,
    trip: Trip,
    packing_list: PackingListSchema,
) -> None:
    """
    Persist validated AI-generated packing items.

    Existing AI-generated packing items are replaced.
    """

    trip_services.clear_ai_generated_packing_items(
        trip=trip,
    )

    for item in packing_list.items:

        trip_services.create_packing_item(
            trip=trip,
            category=PackingCategory(item.category),
            item=item.item,
            quantity=item.quantity,
            reason=item.reason,
            is_ai_generated=True,
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
    
    initial_state = _attach_conversation_context(
        trip=trip,
        state=initial_state,
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
        
        session = ChatService.get_active_session(
            trip=trip,
        )

        assistant_response = final_state.get(
            "assistant_response",
        )

        if (
            session is not None
            and assistant_response
        ):
            ChatService.add_assistant_message(
                session=session,
                content=assistant_response,
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

            if "weather_forecast" in final_state:

                _persist_weather_forecast(
                    trip=trip,
                    weather_forecast=final_state["weather_forecast"],
                )
                
            if "recommendations" in final_state:

                _persist_recommendations(
                    trip=trip,
                    recommendations=final_state["recommendations"],
                )
                
            if "packing_list" in final_state:

                _persist_packing_list(
                    trip=trip,
                    packing_list=final_state["packing_list"],
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

def generate_chat_reply(
    *,
    trip: Trip,
    user_message: str,
) -> str:
    """
    Execute a conversational AI request without running the
    travel planning graph.

    Workflow

    User Message
        ↓
    Persist user message
        ↓
    Build conversation memory
        ↓
    Optimize memory
        ↓
    Chat Agent
        ↓
    Persist assistant message
        ↓
    Return response
    """

    #
    # Ensure an active conversation exists.
    #
    session = ChatService.get_or_create_active_session(
        trip=trip,
    )

    #
    # Persist the user's message.
    #
    ChatService.add_user_message(
        session=session,
        content=user_message,
    )

    #
    # Load conversation history.
    #
    memory = ConversationMemoryAdapter.build_memory(
        session=session,
    )

    #
    # Optimize long conversations.
    #
    manager = ConversationManager()

    memory = manager.optimize_memory(
        memory,
    )

    #
    # Build transcript.
    #
    conversation_context = memory.transcript()

    #
    # Execute conversational agent.
    #
    agent = ChatAgent()

    assistant_response = agent.reply(
        conversation_context=conversation_context,
        user_message=user_message,
    ).strip()

    #
    # Persist assistant reply.
    #
    ChatService.add_assistant_message(
        session=session,
        content=assistant_response,
    )

    return assistant_response