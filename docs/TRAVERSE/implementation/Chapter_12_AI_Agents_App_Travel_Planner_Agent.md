# Chapter 12 — `ai_agents` App + Travel Planner Agent

**Volume 4: AI Layer | Chapter 12 of 29**

> This is where the two worlds built so far — the Django application layer (Chapters 2-10) and the plain-Python `ai/` package (Chapter 11) — meet for the first time. `ai_agents` is a real Django app: it has a model (`AgentRun`), migrations, admin, and Celery tasks. But per Architecture Handbook §4.4, it is **the only** Django app permitted to import from `ai/`. Every other app (including `trips`, which triggers planning) talks to `ai_agents`, never directly to `ai/`. This chapter also introduces the project's first LangGraph node — a single-node graph, deliberately small, with Chapter 17 assembling the full five-agent graph later.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Explain and enforce the "single door" rule structurally: `ai_agents` is the one and only Django app that imports from `ai/`, and know how to verify this with a real check, not just a code review habit.
- Build the first concrete Pydantic schema and prompt (Travel Planner) on top of Chapter 11's generic machinery.
- Wire a single-node LangGraph graph, understanding `StateGraph`, nodes, and the typed state object shared across nodes — the foundation Chapter 17 builds five more nodes onto.
- Trigger AI work asynchronously via Celery (per Architecture Handbook §2.4/§8.8's `202 + polling` pattern), never blocking a Gunicorn worker on an LLM call.
- Persist AI output into Chapter 8's `ItineraryDay`/`ItineraryItem` models through the existing `services.py`, never bypassing it.

---

## 2. Theory

### 2.1 Why `ai_agents` Is a Real Django App When `ai/` Is Not (ELI10)

Recall Chapter 11's specialist-contractor-chef analogy: `ai/` is the contractor, brought in to cook. `ai_agents` is the restaurant's own kitchen manager — an actual employee, who knows the restaurant's systems (Django's ORM, the `Trip` model, Celery), and whose job is specifically to **hire the contractor for a specific order, hand them what they need, and put the finished dish on the right table** (write validated output into `ItineraryDay`/`ItineraryItem`). The kitchen manager needs real employment records (a database table — `AgentRun`) to track "who ordered what, when, and did it succeed." The contractor chef doesn't need any of that; they just cook when called.

### 2.2 What a LangGraph "Node" and "State" Actually Are (ELI10)

Think of a state object as a shared clipboard passed from one specialist to the next. Each specialist (a "node" — a Python function) reads what's already on the clipboard, does their one job, writes their result onto the clipboard, and hands it to the next specialist. A "graph" is just the map of who hands the clipboard to whom, and in what order. This chapter's graph has exactly one specialist on it (the Travel Planner), so the map is trivially simple: start → Travel Planner → end. Chapter 17 adds four more specialists and a more interesting map, matching Architecture Handbook §9.2's diagram — but the *clipboard* (the state shape) is designed now, once, so later chapters extend it rather than redesigning it.

### 2.3 Why Async Dispatch (Celery), Not a Direct Call From the View

Architecture Handbook §2.4 and §8.8 already decided this: an LLM call can take 5-30 seconds (longer here — multiple sequential agent nodes once Chapter 17 lands), and handling it inside the same HTTP request risks tying up a Gunicorn worker, degrading the site for every other user simultaneously. This chapter is where that architectural decision, made on paper back in the Architecture Handbook, becomes real, working code for the first time.

---

## 3. Architecture Decision

**Decision:** `AgentRun` records **every** attempt (not just successes), with a `status` field covering `pending`, `running`, `succeeded`, `failed`, `needs_review` — directly implementing Architecture Handbook §9.8's fallback/retry diagram as real database states, not just an in-memory flow.

**Decision:** The single-door rule is enforced with an actual, automated check (Section 13), not merely stated as a convention — Architecture Handbook §4.4 calls this "a firewall — no other app is allowed to call an LLM directly. Enforced by code review discipline, not by a technical lock." This chapter adds a lightweight technical backstop on top of that code-review discipline: a test that scans every other app's source for `import ai` or `from ai`.

**Alternative considered:** Have `trips` call `ai_agents.services.run_travel_planner()` synchronously from within its own view. **Rejected because:** this would re-introduce the exact blocking-request problem Architecture Handbook §2.4 already solved — the Celery task boundary belongs inside `ai_agents`, triggered by a Celery task dispatch from the view, never a direct synchronous function call for the actual AI work.

**Decision:** The LangGraph state object (`TripPlanningState`) is a `TypedDict`, defined once in `ai/graphs/state.py`, designed with fields for *all five* future agents even though only one (`itinerary_plan`) is populated this chapter.

**Trade-off documented:** this means Chapter 12 ships a state shape with four fields nobody writes to yet — accepted deliberately, because redefining the shared state's shape mid-graph in Chapter 13, 14, 15, and 16 (each adding their own field) would be a worse trade-off: four small, disruptive edits to a shared foundational type versus one slightly-oversized definition now, matching the same "structure before intelligence, sized for the whole plan" instinct already used for `Recommendation.score` in Chapter 10.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `ai/agents/schemas.py` (Pydantic) | Needed before the prompt can describe what shape to return |
| Define `ai/prompts/planner_v1.py` | Needed before the agent function that uses it |
| Define `ai/graphs/state.py` | Needed before any node function, since nodes read/write this shape |
| Define `ai/agents/travel_planner.py` (the node function) | Needed before the graph can be assembled |
| Define `ai/graphs/planning_graph.py` | Needed before `ai_agents` has anything to invoke |
| Define `apps/ai_agents/models.py` (`AgentRun`) | Needed before the service layer can log attempts |
| Define `apps/ai_agents/services.py` | Needed before the Celery task or the view |
| Define `apps/ai_agents/tasks.py` | Needed before the view can dispatch it |
| Define `apps/ai_agents/views.py` | Last — depends on everything above |

---

## 5. File Structure

```
ai/
├── agents/
│   ├── __init__.py
│   ├── schemas.py              # NEW — ItineraryPlanSchema, ItineraryDaySchema, ItineraryItemSchema
│   └── travel_planner.py         # NEW — the node function
├── prompts/
│   └── planner_v1.py              # NEW — concrete PromptTemplate subclass
└── graphs/
    ├── state.py                    # NEW — TripPlanningState TypedDict
    └── planning_graph.py            # NEW — single-node graph for this chapter

apps/ai_agents/
├── __init__.py
├── apps.py
├── models.py                    # AgentRun
├── services.py                   # run_travel_planner() — the ONLY caller of ai/graphs
├── tasks.py                      # Celery task wrapping services.run_travel_planner
├── serializers.py
├── views.py                       # TripPlanView, TripPlanStatusView
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_single_door_enforcement.py   # NEW pattern — architectural boundary test
    └── test_views.py

ai/tests/
├── test_travel_planner_agent.py    # plain pytest, mocked LLM, no Django
└── test_planning_graph.py
```

---

## 6. Folder Location

New AI-layer files under `ai/`; new Django app files under `apps/ai_agents/`. `apps/ai_agents` was already scaffolded empty back in Chapter 2 — this chapter fills it in for the first time.

---

## 7. Terminal Commands

```bash
docker compose exec web pip install langgraph --break-system-packages
# add to requirements/base.txt

docker compose exec web python manage.py makemigrations ai_agents
docker compose exec web python manage.py migrate

docker compose exec web pytest ai/tests -v                 # plain pytest, ai/ layer
docker compose exec web python manage.py test apps.ai_agents  # Django layer
```

---

## 8. Docker Commands

```bash
# Confirm Celery worker is running (DockForge-provided, per Architecture Handbook §10)
docker compose ps celery

docker compose restart web celery   # restart both — the task must be registered on the worker too
```

**Why `celery` must be restarted alongside `web`:** the Celery worker process, like Gunicorn, only discovers tasks at startup — a new task added to `apps/ai_agents/tasks.py` is invisible to an already-running worker until it restarts, the exact same class of "stale process" issue Chapter 5 flagged for signals.

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations ai_agents
Migrations for 'ai_agents':
  apps/ai_agents/migrations/0001_initial.py
    - Create model AgentRun

$ curl -X POST http://localhost:8000/api/v1/trips/<trip_id>/plan/ -H "Authorization: Bearer <access>"
{"task_id": "c9f1...", "agent_run_id": 1, "status": "pending"}

$ curl http://localhost:8000/api/v1/trips/<trip_id>/plan/status/ -H "Authorization: Bearer <access>"
{"status": "succeeded", "agent_run_id": 1, "completed_at": "2026-08-01T10:15:00Z"}
```

---

## 10. Code

### 10.1 `ai/agents/schemas.py`

```python
"""
Pydantic schemas for the Travel Planner Agent's output. This is the
first concrete schema built on Chapter 11's generic
parse_structured_output() machinery.
"""
from datetime import date, time

from pydantic import BaseModel, Field, field_validator


class ItineraryItemSchema(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(default="", max_length=1000)
    start_time: time | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value.strip()


class ItineraryDaySchema(BaseModel):
    day_number: int = Field(..., ge=1)
    date: date
    summary: str = Field(default="", max_length=255)
    items: list[ItineraryItemSchema] = Field(..., min_length=1, max_length=12)


class ItineraryPlanSchema(BaseModel):
    days: list[ItineraryDaySchema] = Field(..., min_length=1)
```

**Why `estimated_cost_usd` uses `ge=0` (Pydantic's own validation) even though Chapter 9's `BudgetLineItem` already has a DB-level `CheckConstraint`**: this is defense in depth applied one layer earlier than usual — rejecting a negative cost *before* it's even accepted as valid AI output means a malformed LLM response never gets the chance to reach the database layer at all, catching the problem at the earliest possible point per Architecture Handbook §9.7's "every agent's final answer is forced through a Pydantic schema... before it's allowed to touch the database."

**Why `items` has `min_length=1, max_length=12`**: an empty day (no activities at all) is almost certainly a sign the model produced degenerate output, and more than 12 items in a single day is implausible for a real itinerary — both bounds catch obviously-wrong output at the schema level, triggering Chapter 11's retry-with-correction flow rather than silently accepting nonsense.

### 10.2 `ai/prompts/planner_v1.py`

```python
"""
Version 1 of the Travel Planner prompt. Per Architecture Handbook
§9.4, prompts are never edited in place once in use — a v2 would be
a new file, never a modification of this one.
"""
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a professional travel planning assistant.
Given a trip's dates, destinations, and traveler preferences, produce
a realistic, well-paced day-by-day itinerary.

Rules:
- Respond with ONLY valid JSON matching the provided schema.
- Each day must have between 1 and 6 realistic, distinct activities.
- Do not invent destinations not mentioned in the trip context.
- Estimated costs should be reasonable for the destination(s) given.
- Never include text outside the JSON object."""


class PlannerPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="travel_planner", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(
        self, *, trip_title: str, start_date: str, end_date: str,
        destination_names: list[str], budget_style: str, travel_pace: str,
        interests: list[str],
    ) -> str:
        destinations = ", ".join(destination_names) or "unspecified"
        interest_list = ", ".join(interests) or "general sightseeing"
        return (
            f"Trip: {trip_title}\n"
            f"Dates: {start_date} to {end_date}\n"
            f"Destinations: {destinations}\n"
            f"Traveler budget style: {budget_style}\n"
            f"Preferred pace: {travel_pace}\n"
            f"Interests: {interest_list}\n\n"
            f"Produce a complete day-by-day itinerary for this trip."
        )
```

**Why `render_user_prompt` takes explicit, named, keyword-only parameters instead of accepting the raw `Trip`/`Profile` Django model instances**: this keeps `ai/prompts/` completely free of any dependency on Django models, preserving Chapter 11's zero-Django-dependency boundary — `ai_agents` (Section 10.7) is responsible for extracting the plain values a `Trip`/`Profile` holds and passing them in, not `ai/` reaching back into Django to fetch them itself.

### 10.3 `ai/graphs/state.py`

```python
"""
Shared LangGraph state, sized for the FULL five-agent graph
(Architecture Handbook §9.2), even though only itinerary_plan is
populated starting this chapter. See Chapter 12 Architecture
Decision for why this is sized ahead rather than grown incrementally.
"""
from typing import TypedDict

from ai.agents.schemas import ItineraryPlanSchema


class TripPlanningState(TypedDict, total=False):
    # --- Input context, populated by ai_agents before the graph runs ---
    trip_title: str
    start_date: str
    end_date: str
    destination_names: list[str]
    budget_style: str
    travel_pace: str
    interests: list[str]

    # --- Populated by Chapter 12's Travel Planner node ---
    itinerary_plan: ItineraryPlanSchema

    # --- Reserved for Chapter 13 onward — deliberately present now, unused ---
    budget_estimate: dict | None
    weather_forecast: dict | None
    recommendations: list[dict] | None
    packing_list: list[str] | None
```

**Why `total=False`**: a `TypedDict` with `total=True` (the default) requires every key to be present at all times, which is impossible here — the whole point of a multi-node graph is that later fields don't exist yet when the state is first created. `total=False` correctly models "this dict grows as it passes through the graph."

### 10.4 `ai/agents/travel_planner.py`

```python
"""
The Travel Planner Agent — the first LangGraph node in the project.
A node is just a function: (state) -> partial state update.
"""
from ai.agents.schemas import ItineraryPlanSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import TripPlanningState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.planner_v1 import PlannerPromptV1

_prompt = PlannerPromptV1()


def travel_planner_node(state: TripPlanningState, *, client: GroqClient | None = None) -> dict:
    """
    Reads trip context off the state, calls the LLM, validates the
    result, and returns a partial state update (LangGraph merges
    this into the running state — nodes never return the FULL state,
    only what they changed).
    """
    client = client or GroqClient()

    user_prompt = _prompt.render_user_prompt(
        trip_title=state["trip_title"],
        start_date=state["start_date"],
        end_date=state["end_date"],
        destination_names=state["destination_names"],
        budget_style=state["budget_style"],
        travel_pace=state["travel_pace"],
        interests=state["interests"],
    )

    plan: ItineraryPlanSchema = parse_structured_output(
        client=client,
        system_prompt=_prompt.system_prompt,
        user_prompt=user_prompt,
        schema=ItineraryPlanSchema,
        temperature=0.4,
    )

    return {"itinerary_plan": plan}
```

**Why the node returns `{"itinerary_plan": plan}` — a partial dict — rather than the entire modified state**: this is a LangGraph convention, not a stylistic choice — `StateGraph` nodes are expected to return only the keys they changed, and the graph runtime merges this into the shared state automatically. Returning the full state would work for a single-node graph but breaks the composability Chapter 17 depends on, where multiple nodes each contribute their own slice.

**Why `client` is an optional, injectable parameter here too**: same dependency-injection reasoning as Chapter 11's `parse_structured_output` — Section 14's tests pass in a mock client; production code (Section 10.8) lets it default to a real one.

### 10.5 `ai/graphs/planning_graph.py`

```python
"""
The trip planning graph. This chapter: ONE node. Chapter 17: five
nodes, matching Architecture Handbook §9.2's full diagram.
"""
from langgraph.graph import END, START, StateGraph

from ai.agents.travel_planner import travel_planner_node
from ai.graphs.state import TripPlanningState


def build_planning_graph():
    graph = StateGraph(TripPlanningState)
    graph.add_node("travel_planner", travel_planner_node)
    graph.add_edge(START, "travel_planner")
    graph.add_edge("travel_planner", END)
    return graph.compile()


def run_planning_graph(initial_state: TripPlanningState) -> TripPlanningState:
    compiled_graph = build_planning_graph()
    return compiled_graph.invoke(initial_state)
```

**Why `build_planning_graph()` and `run_planning_graph()` are separate functions**: `build_planning_graph()` is useful on its own for testing the graph's *shape* (Section 14's `test_planning_graph.py` checks nodes/edges without ever invoking an LLM); `run_planning_graph()` is the convenience entry point `ai_agents` actually calls. Splitting them mirrors the same "build vs. use" separation as Chapter 11's `GroqClient.__init__` vs `.call()`.

### 10.6 `apps/ai_agents/models.py`

```python
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class AgentType(models.TextChoices):
    TRAVEL_PLANNER = "travel_planner", "Travel Planner"
    BUDGET = "budget", "Budget"                 # Chapter 13
    WEATHER = "weather", "Weather"               # Chapter 14
    RECOMMENDATION = "recommendation", "Recommendation"  # Chapter 15
    PACKING = "packing", "Packing"               # Chapter 16
    FULL_GRAPH = "full_graph", "Full Planning Graph"      # Chapter 17


class AgentRunStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    NEEDS_REVIEW = "needs_review", "Needs Review"


class AgentRun(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Logs every attempt to run an AI agent against a trip — not just
    successes. Directly implements Architecture Handbook §9.8's
    retry/fallback diagram as real, queryable database state.
    """
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="agent_runs",
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="agent_runs",
    )
    agent_type = models.CharField(max_length=30, choices=AgentType.choices)
    status = models.CharField(
        max_length=20, choices=AgentRunStatus.choices, default=AgentRunStatus.PENDING, db_index=True,
    )
    input_snapshot = models.JSONField(
        default=dict,
        help_text="The exact state passed into the graph, for reproducibility/debugging.",
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trip", "agent_type", "created_at"]),
        ]
        verbose_name = "Agent Run"
        verbose_name_plural = "Agent Runs"

    def __str__(self) -> str:
        return f"{self.agent_type} run for {self.trip.title} ({self.status})"
```

**Why `triggered_by` uses `SET_NULL`, not `CASCADE`**: unlike `Trip.user` (Chapter 7, `CASCADE`), an `AgentRun`'s historical record has ongoing value (debugging, analytics — Chapter 24) even after the triggering user's account is deleted; losing *who* triggered it is acceptable, losing the run record itself is not — the exact same reasoning already established for `ItineraryItem.destination` in Chapter 8, applied to a different relationship here.

**Why `input_snapshot` stores the exact state passed into the graph**: this makes every `AgentRun` fully reproducible for debugging — if a user reports a bad itinerary, the exact inputs that produced it are on record, not reconstructed after the fact from a `Trip`'s *current* (possibly since-changed) state.

### 10.7 `apps/ai_agents/services.py`

```python
"""
THE only Django-facing entry point into the ai/ package. No other
app is permitted to import from ai/ — see Chapter 12 Architecture
Decision and the enforcement test in tests/test_single_door_enforcement.py.
"""
import logging

from django.utils import timezone

from ai.exceptions import LLMCallFailed, StructuredOutputInvalid
from ai.graphs.planning_graph import run_planning_graph
from apps.ai_agents.models import AgentRun, AgentType, AgentRunStatus
from apps.itinerary import services as itinerary_services
from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip

logger = logging.getLogger("apps.ai_agents")


def _build_initial_state(trip: Trip) -> dict:
    profile = trip.user.profile
    return {
        "trip_title": trip.title,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "destination_names": [d.name for d in trip.destinations.all()],
        "budget_style": profile.budget_style,
        "travel_pace": profile.travel_pace,
        "interests": profile.interests,
    }


def _persist_itinerary_plan(*, trip: Trip, plan) -> None:
    """
    Writes validated AI output into Chapter 8's models, EXCLUSIVELY
    through itinerary_services — never a raw ItineraryDay.objects.create()
    here, keeping the "structure before intelligence" contract intact:
    the AI layer conforms to the existing data layer, not the reverse.
    """
    for day_schema in plan.days:
        day, _ = ItineraryDay.objects.update_or_create(
            trip=trip, day_number=day_schema.day_number,
            defaults={"date": day_schema.date, "summary": day_schema.summary},
        )
        day.items.all().delete()  # replace, since this is a fresh AI-generated plan
        for item_schema in day_schema.items:
            itinerary_services.add_item_to_day(
                day=day,
                title=item_schema.title,
                description=item_schema.description,
                start_time=item_schema.start_time,
                estimated_cost_usd=item_schema.estimated_cost_usd,
                is_ai_generated=True,
            )


def run_travel_planner(*, trip: Trip, triggered_by=None) -> AgentRun:
    initial_state = _build_initial_state(trip)
    agent_run = AgentRun.objects.create(
        trip=trip, triggered_by=triggered_by, agent_type=AgentType.TRAVEL_PLANNER,
        status=AgentRunStatus.RUNNING, input_snapshot=initial_state, started_at=timezone.now(),
    )

    try:
        final_state = run_planning_graph(initial_state)
        _persist_itinerary_plan(trip=trip, plan=final_state["itinerary_plan"])
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
    finally:
        agent_run.completed_at = timezone.now()
        agent_run.save(update_fields=["status", "error_message", "completed_at"])

    return agent_run
```

**Why `_persist_itinerary_plan` deletes and recreates a day's items (`day.items.all().delete()`) rather than trying to merge AI output with any existing manual edits**: for this first version, an AI planning run is treated as "generate a fresh plan," not "merge with what's there" — attempting a smart merge (preserving user edits while replacing AI-generated ones) is a genuinely harder problem explicitly deferred; `is_ai_generated` (Chapter 8) exists precisely so a *future* smarter merge strategy could distinguish AI rows from user rows, but this chapter keeps the first implementation simple and clearly-scoped, flagged here rather than silently declared "done."

**Why this function is a `try/except/else/finally` with three distinct outcomes, exactly matching Architecture Handbook §9.8's diagram**: `StructuredOutputInvalid` → `needs_review` (schema validation exhausted its one retry), `LLMCallFailed` → `failed` (network/provider exhausted its retries), success → `succeeded`, and `finally` always stamps `completed_at` and saves — no code path leaves an `AgentRun` stuck in `running` forever, which would otherwise be a silent, hard-to-notice bug.

### 10.8 `apps/ai_agents/tasks.py`

```python
"""
Celery task wrapping the synchronous services.run_travel_planner()
call. This is the ONE place in the entire project where an LLM-
calling function is invoked outside of a request/response cycle,
per Architecture Handbook §2.4/§8.8.
"""
from celery import shared_task


@shared_task(bind=True, max_retries=0)
def run_travel_planner_task(self, trip_id: str, user_id: int | None = None):
    from apps.ai_agents import services
    from apps.trips.models import Trip
    from django.contrib.auth import get_user_model

    trip = Trip.objects.get(pk=trip_id)
    user = get_user_model().objects.filter(pk=user_id).first() if user_id else None

    agent_run = services.run_travel_planner(trip=trip, triggered_by=user)
    return str(agent_run.id)
```

**Why `max_retries=0` at the Celery task level, when `GroqClient` already retries internally (Chapter 11)**: retrying at two independent layers (Celery re-queuing the whole task, and `tenacity` retrying the individual HTTP call inside it) would compound delays unpredictably and risk duplicate side effects (writing itinerary data twice) — retry policy belongs at exactly one layer, and Chapter 11 already owns it at the granularity that matters (the LLM call itself), so the Celery task layer deliberately does not add a second, redundant retry mechanism.

**Why the imports (`Trip`, `services`, `get_user_model`) are inside the function body, not at module level**: Celery tasks are often collected/registered very early in the app-loading process — deferring Django-model imports until the task actually runs avoids a class of `AppRegistryNotReady` issues at worker startup, a standard, common Celery+Django convention worth calling out explicitly for anyone new to the combination.

### 10.9 `apps/ai_agents/serializers.py`

```python
from rest_framework import serializers

from apps.ai_agents.models import AgentRun


class AgentRunStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentRun
        fields = ["id", "agent_type", "status", "error_message", "started_at", "completed_at"]
        read_only_fields = fields
```

### 10.10 `apps/ai_agents/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.models import AgentRun, AgentType
from apps.ai_agents.serializers import AgentRunStatusSerializer
from apps.ai_agents.tasks import run_travel_planner_task
from apps.trips.models import Trip


class TripPlanView(APIView):
    """
    Triggers AI planning ASYNCHRONOUSLY. Returns 202 + task/run ids
    immediately — per Architecture Handbook §8.8's request/response
    diagram, this endpoint never waits for the LLM.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        task = run_travel_planner_task.delay(trip_id=str(trip.id), user_id=request.user.id)
        return Response(
            {"task_id": task.id, "status": "pending"}, status=http_status.HTTP_202_ACCEPTED,
        )


class TripPlanStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        latest_run = (
            AgentRun.objects.filter(trip=trip, agent_type=AgentType.TRAVEL_PLANNER)
            .order_by("-created_at")
            .first()
        )
        if latest_run is None:
            return Response({"status": "not_started"})
        return Response(AgentRunStatusSerializer(latest_run).data)
```

**Why `TripPlanView` returns the Celery `task.id`, while `TripPlanStatusView` looks up the *latest* `AgentRun` by trip rather than by that task id**: a client polling for status doesn't need to know or store the Celery task id at all — it only needs to know "what's the current state of planning for this trip," which the `AgentRun` table already answers directly and more durably (Celery task results can expire from the result backend; the `AgentRun` row does not).

### 10.11 `apps/ai_agents/urls.py`

```python
from django.urls import path

from apps.ai_agents.views import TripPlanStatusView, TripPlanView

app_name = "ai_agents"

urlpatterns = [
    path("<uuid:trip_pk>/plan/", TripPlanView.as_view(), name="plan"),
    path("<uuid:trip_pk>/plan/status/", TripPlanStatusView.as_view(), name="plan-status"),
]
```

### 10.12 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.ai_agents.urls")),
```

### 10.13 `apps/ai_agents/admin.py`

```python
from django.contrib import admin

from apps.ai_agents.models import AgentRun


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ["trip", "agent_type", "status", "triggered_by", "started_at", "completed_at"]
    list_filter = ["agent_type", "status"]
    search_fields = ["trip__title"]
    readonly_fields = ["input_snapshot", "created_at", "updated_at", "started_at", "completed_at"]
```

---

## 11. Code Walkthrough

- **`_build_initial_state` lives in `apps/ai_agents/services.py`, not in `ai/`**: this is the precise line where Django model data (`Trip`, `Profile`) gets translated into plain values before crossing into the Django-free `ai/` package — the boundary from Chapter 11's Architecture Decision is visible here as a concrete function, not just an abstract rule.
- **`travel_planner_node` and `run_travel_planner` (services.py) have similar-sounding names but different jobs**: the former is a pure LangGraph node (Django-unaware, testable with plain pytest); the latter is the Django-aware orchestrator that creates the `AgentRun`, calls the graph, and persists results. Keeping the naming close but the responsibility strictly separated is intentional — it should always be obvious from the file location (`ai/` vs `apps/ai_agents/`) which one you're looking at.
- **The single-node graph (this chapter) and the eventual five-node graph (Chapter 17) share the exact same `TripPlanningState` shape**: because Section 10.3 sized the state ahead of need, `ai_agents/services.py`'s `_build_initial_state` function will need zero changes when Chapter 17 arrives — only `ai/graphs/planning_graph.py` grows new nodes and edges.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `celery.exceptions.NotRegistered: 'apps.ai_agents.tasks.run_travel_planner_task'` | Celery worker not restarted after adding the task | `docker compose restart celery` |
| `AgentRun` stuck in `running` forever | An unhandled exception type escaped the `try/except` in `run_travel_planner` (e.g., a bug outside `StructuredOutputInvalid`/`LLMCallFailed`) | This is exactly why `finally` stamps `completed_at` regardless — but an *uncaught* exception still propagates; check Celery worker logs for a traceback and consider whether a new exception type needs handling |
| Itinerary items don't reflect the new plan after re-running `/plan/` | Confusing "should merge with existing" for "always this chapter's behavior: replace" | Expected — see 10.7's documented "fresh regenerate" scope; a smarter merge is explicitly future work |
| `ImportError` when any app other than `ai_agents` tries `from ai.clients.groq_client import GroqClient` | This is the single-door rule being violated | Route the logic through `apps.ai_agents.services` instead — no other app should import from `ai/` at all |

---

## 13. Debugging

```bash
# 1. THE single-door structural check — scan every app's source for forbidden ai/ imports
docker compose exec web python -c "
import pathlib, re
violations = []
for path in pathlib.Path('apps').rglob('*.py'):
    if 'ai_agents' in path.parts:
        continue
    text = path.read_text()
    if re.search(r'^\s*(from|import)\s+ai(\.|$| )', text, re.MULTILINE):
        violations.append(str(path))
print('Violations:', violations or 'NONE — single-door rule holds')
"

# 2. Manually trigger the graph in a Django shell, bypassing Celery, for fast iteration
docker compose exec web python manage.py shell -c "
from apps.ai_agents import services
from apps.trips.models import Trip
trip = Trip.objects.first()
run = services.run_travel_planner(trip=trip)
print(run.status, run.error_message)
"

# 3. Inspect the Celery worker's live logs while a task runs
docker compose logs -f celery
```

**Rollback strategy:** since `_persist_itinerary_plan` fully replaces a day's items rather than partially patching them, and every `AgentRun` records its `input_snapshot`, recovering from a bad AI-generated plan is always possible by re-running `run_travel_planner` — the previous (bad) itinerary items are simply overwritten by the next successful run, with no manual cleanup needed.

---

## 14. Testing

### 14.1 `ai/tests/test_travel_planner_agent.py` (plain pytest, zero Django)

```python
from datetime import date
from unittest.mock import MagicMock

from ai.agents.schemas import ItineraryPlanSchema
from ai.agents.travel_planner import travel_planner_node


def test_travel_planner_node_returns_partial_state_update():
    fake_client = MagicMock()
    fake_client.call.return_value = (
        '{"days": [{"day_number": 1, "date": "2026-06-01", "summary": "Arrival", '
        '"items": [{"title": "Check into hotel", "description": "", "estimated_cost_usd": 100}]}]}'
    )

    state = {
        "trip_title": "Japan Trip", "start_date": "2026-06-01", "end_date": "2026-06-05",
        "destination_names": ["Tokyo"], "budget_style": "moderate", "travel_pace": "balanced",
        "interests": ["food"],
    }

    result = travel_planner_node(state, client=fake_client)

    assert "itinerary_plan" in result
    assert isinstance(result["itinerary_plan"], ItineraryPlanSchema)
    assert result["itinerary_plan"].days[0].day_number == 1
```

### 14.2 `ai/tests/test_planning_graph.py`

```python
from ai.graphs.planning_graph import build_planning_graph


def test_graph_compiles_with_expected_node():
    graph = build_planning_graph()
    # get_graph() exposes the underlying node/edge structure for
    # inspection without ever invoking an LLM
    node_names = set(graph.get_graph().nodes.keys())
    assert "travel_planner" in node_names
```

### 14.3 `apps/ai_agents/tests/test_single_door_enforcement.py` (the architectural boundary test)

```python
import pathlib
import re

from django.test import SimpleTestCase


class SingleDoorEnforcementTests(SimpleTestCase):
    """
    Structural proof that Architecture Handbook §4.4's 'firewall' is
    actually held, not just documented. Fails loudly if any app
    other than ai_agents imports from ai/.
    """

    def test_no_other_app_imports_from_ai_package(self):
        violations = []
        apps_root = pathlib.Path(__file__).resolve().parents[3] / "apps"
        for path in apps_root.rglob("*.py"):
            if "ai_agents" in path.parts:
                continue
            text = path.read_text()
            if re.search(r"^\s*(from|import)\s+ai(\.|$| )", text, re.MULTILINE):
                violations.append(str(path))

        self.assertEqual(violations, [], f"Apps importing from ai/ outside ai_agents: {violations}")
```

### 14.4 `apps/ai_agents/tests/test_services.py`

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.ai_agents.models import AgentRun, AgentRunStatus
from apps.itinerary.models import ItineraryItem
from apps.trips.models import Trip
from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema
from ai.exceptions import LLMCallFailed, StructuredOutputInvalid

User = get_user_model()


class RunTravelPlannerServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="ai@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test Trip", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3),
        )

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_successful_run_persists_itinerary_and_marks_succeeded(self, mock_run_graph):
        mock_run_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(
                days=[
                    ItineraryDaySchema(
                        day_number=1, date=date(2026, 6, 1), summary="Arrival",
                        items=[ItineraryItemSchema(title="Check in", estimated_cost_usd=100)],
                    )
                ]
            )
        }

        agent_run = services.run_travel_planner(trip=self.trip, triggered_by=self.user)

        self.assertEqual(agent_run.status, AgentRunStatus.SUCCEEDED)
        self.assertEqual(ItineraryItem.objects.filter(day__trip=self.trip).count(), 1)
        self.assertTrue(ItineraryItem.objects.get(day__trip=self.trip).is_ai_generated)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_structured_output_invalid_marks_needs_review(self, mock_run_graph):
        mock_run_graph.side_effect = StructuredOutputInvalid("bad output")

        agent_run = services.run_travel_planner(trip=self.trip)

        self.assertEqual(agent_run.status, AgentRunStatus.NEEDS_REVIEW)
        self.assertIn("bad output", agent_run.error_message)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_llm_call_failed_marks_failed(self, mock_run_graph):
        mock_run_graph.side_effect = LLMCallFailed("network down")

        agent_run = services.run_travel_planner(trip=self.trip)

        self.assertEqual(agent_run.status, AgentRunStatus.FAILED)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_completed_at_always_set_regardless_of_outcome(self, mock_run_graph):
        mock_run_graph.side_effect = LLMCallFailed("network down")
        agent_run = services.run_travel_planner(trip=self.trip)
        self.assertIsNotNone(agent_run.completed_at)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_rerunning_replaces_previous_ai_items(self, mock_run_graph):
        mock_run_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                    ItineraryItemSchema(title="First plan item")
                ])
            ])
        }
        services.run_travel_planner(trip=self.trip)
        self.assertEqual(ItineraryItem.objects.filter(day__trip=self.trip).count(), 1)

        mock_run_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                    ItineraryItemSchema(title="Regenerated item A"),
                    ItineraryItemSchema(title="Regenerated item B"),
                ])
            ])
        }
        services.run_travel_planner(trip=self.trip)
        items = ItineraryItem.objects.filter(day__trip=self.trip)
        self.assertEqual(items.count(), 2)
        self.assertNotIn("First plan item", items.values_list("title", flat=True))
```

### 14.5 `apps/ai_agents/tests/test_views.py`

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_agents.models import AgentRun, AgentRunStatus, AgentType
from apps.trips.models import Trip

User = get_user_model()


class TripPlanViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="v@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3),
        )
        login = self.client.post(reverse("accounts:login"), {"email": "v@example.com", "password": "pass1234"})
        self.token = login.data["tokens"]["access"]

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    @patch("apps.ai_agents.views.run_travel_planner_task.delay")
    def test_plan_endpoint_returns_202_immediately(self, mock_delay):
        mock_delay.return_value.id = "fake-task-id"
        response = self.client.post(
            reverse("ai_agents:plan", kwargs={"trip_pk": self.trip.pk}), **self._auth()
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["task_id"], "fake-task-id")
        mock_delay.assert_called_once()

    def test_status_endpoint_returns_not_started_before_any_run(self):
        response = self.client.get(
            reverse("ai_agents:plan-status", kwargs={"trip_pk": self.trip.pk}), **self._auth()
        )
        self.assertEqual(response.data["status"], "not_started")

    def test_status_endpoint_reflects_latest_run(self):
        AgentRun.objects.create(
            trip=self.trip, agent_type=AgentType.TRAVEL_PLANNER, status=AgentRunStatus.SUCCEEDED,
        )
        response = self.client.get(
            reverse("ai_agents:plan-status", kwargs={"trip_pk": self.trip.pk}), **self._auth()
        )
        self.assertEqual(response.data["status"], "succeeded")
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add ai/agents/ ai/prompts/planner_v1.py ai/graphs/ apps/ai_agents/ config/urls.py requirements/base.txt
git commit -m "feat(ai_agents): bridge app + Travel Planner Agent + first LangGraph node

- ai/agents/schemas.py: ItineraryPlanSchema (first concrete schema
  on Chapter 11's generic parser), with bounds (1-12 items/day)
  that reject obviously-degenerate output at the schema level
- ai/prompts/planner_v1.py: first concrete prompt; render_user_prompt
  takes plain values only, never Django model instances, preserving
  Chapter 11's zero-Django boundary
- ai/graphs/state.py: TripPlanningState sized for the FULL five-agent
  graph now, even though only itinerary_plan is populated this
  chapter — avoids four disruptive edits to shared state later
- ai/graphs/planning_graph.py: first LangGraph StateGraph, one node,
  build/run split for testability
- apps/ai_agents: the ONLY Django app permitted to import ai/ per
  Architecture Handbook §4.4 — now backed by an actual automated
  test (test_single_door_enforcement.py), not just convention
- AgentRun model: logs every attempt, not just successes, directly
  implementing §9.8's retry/fallback diagram as real DB states
  (pending/running/succeeded/failed/needs_review)
- services.run_travel_planner: try/except/else/finally covering all
  three documented outcomes; completed_at always stamped, no run
  left stuck in 'running'
- Celery task dispatch (202 + polling), single retry layer (Celery
  does NOT re-retry on top of tenacity's internal retries)
- Full coverage across both plain-pytest (ai/) and Django (ai_agents)
  test suites

Chapter 12 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `ItineraryPlanSchema` enforces sane bounds (min/max items per day), rejecting degenerate output at the schema level
- [ ] `PlannerPromptV1.render_user_prompt` accepts only plain values, no Django model instances
- [ ] `TripPlanningState` includes reserved fields for Chapters 13-16, documented as intentional
- [ ] `build_planning_graph()`/`run_planning_graph()` split, graph shape testable without any LLM call
- [ ] `AgentRun` covers all 5 statuses; `run_travel_planner` never leaves a run stuck in `running`
- [ ] Single-door rule enforced by an automated test, not just documentation — confirmed passing
- [ ] Celery task registered, worker restarted, `/plan/` returns `202` immediately (never blocks)
- [ ] `/plan/status/` correctly reports `not_started` before any run exists
- [ ] Re-running the planner replaces (not merges with) previous AI-generated items — documented, tested behavior
- [ ] All tests passing in both `ai/tests` (pytest) and `apps.ai_agents` (Django)
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 13 — Budget Agent** adds the second node to the planning graph, writing into Chapter 9's `Budget`/`BudgetLineItem` models the same way this chapter writes into Chapter 8's itinerary models — through `services.py`, never a raw model write from the AI layer. This is also the first agent whose output is *purely numeric* rather than free-form text/description, and the first chapter to reckon directly with Chapter 9's documented signal gap (bulk operations bypassing Django signals) now that an AI agent is about to write line items programmatically. Say **"Continue to Chapter 13"** when ready.
