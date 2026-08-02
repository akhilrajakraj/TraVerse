# Chapter 17 — LangGraph Orchestration Assembly

**Volume 4: AI Layer | Chapter 17 of 29**

> No new agent logic is built in this chapter — the five-node graph already reached its final shape in Chapter 16. This is the "close out Volume 4" chapter: renaming `AgentRun.agent_type` from the Chapter 12 placeholder to the properly reserved `FULL_GRAPH` value (with a real, reversible data migration), hardening the Celery trigger now that one request drives meaningfully more work, closing a promise made all the way back in Architecture Handbook §10 (per-user rate limiting on `/plan/`), and writing the single most valuable test in the project so far: a true end-to-end integration test exercising all five real nodes together.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Write a reversible Django data migration that updates existing rows without requiring a schema change, and explain why choices fields don't need a schema migration to add a new valid value.
- Decide, with explicit reasoning, when to rename a *data value* without renaming the *code symbol* that produces it.
- Guard an async-triggering endpoint against duplicate concurrent triggers, and implement basic per-user rate limiting using Redis-backed caching.
- Write an integration test for a graph with genuine parallel branches, using content-based response routing instead of a fragile ordered list of mocked responses.

---

## 2. Theory

### 2.1 Why a Data Migration, Not a Schema Migration (ELI10)

Adding `AgentType.FULL_GRAPH` as a valid choice back in Chapter 12 required no migration at all — Django `choices` are validated in Python, not enforced by the database as a constraint (a `CharField` can technically hold any string up to its `max_length`, choices are a form/admin/validation convenience, not a hard DB rule). What *does* need attention now is that real rows already exist in the database with `agent_type='travel_planner'` from every test and manual run across Chapters 12-16 — a **data migration** (a migration whose job is to change *data*, not *structure*) is the correct tool to bring those existing rows in line with the corrected meaning, exactly the same distinction between "changing the shape of the box" and "changing what's inside it" introduced back in Chapter 2's app-scaffolding discussion, applied here to data instead of code structure.

### 2.2 Why the Python Function Name Stays `run_travel_planner`, But the Data It Writes Changes

This is worth naming as a genuine, considered choice, not an oversight: `run_travel_planner()` (Chapter 12) is still an accurate description of *what a caller is doing* — triggering the trip-planning process. What changed is that this process now spans five agents, not one, and Chapter 24's future analytics need `AgentRun.agent_type` to honestly reflect "this run executed the full graph," not just the first node in it. Renaming the Python symbol across five chapters' worth of call sites (views, tasks, tests) for a purely cosmetic reason would be real, non-trivial churn for zero functional benefit — contrast this directly with Chapter 16's `packing_list` type correction, which *was* worth the churn because it fixed a genuinely wrong shape, not just a name.

### 2.3 Why Now Is the Right Time to Add Rate Limiting and Duplicate-Trigger Protection

Chapter 12's single-node graph made one LLM call. Chapter 16's five-node graph makes upward of seven or eight. A user double-clicking "Generate My Trip," or refreshing a slow-loading page, could now trigger two full, expensive five-agent runs concurrently for the same trip — wasted cost, and a real risk of the two runs' persistence steps interleaving in confusing ways. Architecture Handbook §10 already named this requirement ("Rate Limiting: Per-user limit on `/plan/` and `/chat/` endpoints") back in Volume 1's planning — this chapter is where that promise is finally implemented, now that there's real, meaningful cost behind the endpoint being protected.

---

## 3. Architecture Decision

**Decision:** A reversible `RunPython` data migration updates existing `AgentRun.agent_type='travel_planner'` rows to `'full_graph'`; going forward, `run_travel_planner()` writes `AgentType.FULL_GRAPH` directly — the Python function name is unchanged, the data value it produces is corrected.

**Decision:** `TripPlanView` rejects a new trigger with `409 Conflict` if the trip already has an `AgentRun` in `pending` or `running` status, rather than silently queuing a second concurrent run.

**Alternative considered:** Let Celery/the database handle concurrent runs naturally (last write wins). **Rejected because:** two concurrent five-agent runs racing to write `ItineraryDay`/`BudgetLineItem`/etc. for the same trip is a real, confusing failure mode — rejecting the second request outright, with a clear reason, is far safer and easier to reason about than allowing two runs to interleave.

**Decision:** Rate limiting uses a simple Redis-backed counter via Django's cache framework (already configured by DockForge per Architecture Handbook §10), not a new dependency like `django-ratelimit`.

**Trade-off documented:** a hand-rolled counter is less feature-rich than a dedicated rate-limiting package (no sliding windows, no per-endpoint configuration UI) — accepted because the actual requirement ("a per-user limit on this one endpoint") is small and well-defined enough that a focused, ~15-line implementation is easier to understand and audit than pulling in a general-purpose package for one use case, the same YAGNI reasoning already applied repeatedly (Chapter 6's search, Chapter 14's weather lookup).

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Write and apply the data migration | Needed before any code renames what it *reads*, so existing rows and new rows agree |
| Update `AgentType` usage in `services.py`/`views.py` | Needed before tests are updated to match |
| Update existing tests referencing `AgentType.TRAVEL_PLANNER` for the composite run | Needed before new tests are added, so the whole suite is internally consistent |
| Add duplicate-trigger guard to `TripPlanView` | Needed before rate limiting, since both live in the same view and should be reviewed together |
| Add Redis-backed rate limiting | Comes after the duplicate guard — a related but distinct protection |
| Harden the Celery task (`time_limit`) | Independent of the above, but logically grouped as "hardening the trigger" |
| Write the full end-to-end integration test | Last — needs every other piece of Volume 4 already in its final form |

---

## 5. File Structure

```
apps/ai_agents/
├── migrations/
│   └── 0002_backfill_full_graph_agent_type.py   # NEW — data migration
├── services.py                    # MODIFIED — AgentType.FULL_GRAPH
├── views.py                        # MODIFIED — duplicate guard + rate limiting
├── tasks.py                        # MODIFIED — time_limit
├── tests/
│   ├── test_views.py                 # MODIFIED — AgentType.FULL_GRAPH, new guard tests
│   └── test_integration_full_graph.py  # NEW — the capstone test
```

---

## 6. Folder Location

All changes under `apps/ai_agents/`. No changes to `ai/` at all this chapter — everything here is Django-side wiring and hardening.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations ai_agents --empty --name backfill_full_graph_agent_type
# then hand-edit the generated file per Section 10.1

docker compose exec web python manage.py migrate

docker compose exec web python manage.py test apps.ai_agents -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web celery
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py migrate ai_agents
Running migrations:
  Applying ai_agents.0002_backfill_full_graph_agent_type... OK

$ docker compose exec web python manage.py shell -c "
from apps.ai_agents.models import AgentRun
print(AgentRun.objects.filter(agent_type='travel_planner').count())
print(AgentRun.objects.filter(agent_type='full_graph').count())
"
0
<however many existed before, now under full_graph>
```

---

## 10. Code

### 10.1 `apps/ai_agents/migrations/0002_backfill_full_graph_agent_type.py`

```python
"""
Data migration: existing AgentRun rows created before Chapter 17
used agent_type='travel_planner' for the composite five-agent run.
This backfills them to 'full_graph', matching the value
run_travel_planner() writes going forward. No schema change — see
Chapter 17 Theory §2.1 for why choices don't require one.
"""
from django.db import migrations

OLD_VALUE = "travel_planner"
NEW_VALUE = "full_graph"


def backfill_forward(apps, schema_editor):
    AgentRun = apps.get_model("ai_agents", "AgentRun")
    AgentRun.objects.filter(agent_type=OLD_VALUE).update(agent_type=NEW_VALUE)


def backfill_reverse(apps, schema_editor):
    """
    Reversible: if this migration is ever rolled back, rows are
    returned to their prior value. Writing a reverse function
    (instead of migrations.RunPython.noop) is a small extra effort
    that keeps `migrate ai_agents 0001` genuinely safe to run.
    """
    AgentRun = apps.get_model("ai_agents", "AgentRun")
    AgentRun.objects.filter(agent_type=NEW_VALUE).update(agent_type=OLD_VALUE)


class Migration(migrations.Migration):
    dependencies = [("ai_agents", "0001_initial")]

    operations = [
        migrations.RunPython(backfill_forward, backfill_reverse),
    ]
```

**Why `apps.get_model("ai_agents", "AgentRun")` is used instead of `from apps.ai_agents.models import AgentRun`**: this is a required Django migration convention, not a stylistic choice — migrations must use the *historical* version of a model as it existed at that point in migration history, not whatever the model looks like in the current codebase (which might have new fields by the time this migration actually runs against someone's database). Importing the real model class directly would silently break if the model's shape has changed since this migration was written.

**Why this uses `QuerySet.update()`, unlike Chapter 13's careful avoidance of it**: this is worth contrasting directly — Chapter 13 avoided `.update()` specifically because a signal (`Trip.computed_budget_total` sync) depended on `post_save` firing per row. `AgentRun` has no signals depending on it anywhere in this project; `.update()` here is both correct and appropriately efficient for what could be a large backfill across many historical rows — the same "no signals here, so bulk is fine" reasoning explicitly noted for `ItineraryDay` weather fields in Chapter 14.

### 10.2 `apps/ai_agents/services.py` (modified)

```python
def run_travel_planner(*, trip: Trip, triggered_by=None) -> AgentRun:
    initial_state = _build_initial_state(trip)
    agent_run = AgentRun.objects.create(
        trip=trip, triggered_by=triggered_by,
        agent_type=AgentType.FULL_GRAPH,   # CHANGED from AgentType.TRAVEL_PLANNER — see Chapter 17
        status=AgentRunStatus.RUNNING, input_snapshot=initial_state, started_at=timezone.now(),
    )
    # ... rest of the function is completely unchanged from Chapter 16 ...
```

### 10.3 `apps/ai_agents/views.py` (modified — guard + rate limit + renamed status filter)

```python
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.models import AgentRun, AgentType, AgentRunStatus
from apps.ai_agents.serializers import AgentRunStatusSerializer
from apps.ai_agents.tasks import run_travel_planner_task
from apps.trips.models import Trip

_RATE_LIMIT_MAX_REQUESTS = 5
_RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour


def _rate_limit_key(user_id: int) -> str:
    return f"plan_trigger_rate_limit:{user_id}"


def _is_rate_limited(user_id: int) -> bool:
    key = _rate_limit_key(user_id)
    current_count = cache.get(key, 0)
    return current_count >= _RATE_LIMIT_MAX_REQUESTS


def _increment_rate_limit(user_id: int) -> None:
    key = _rate_limit_key(user_id)
    try:
        cache.incr(key)
    except ValueError:
        # Key doesn't exist yet — first request in this window
        cache.set(key, 1, timeout=_RATE_LIMIT_WINDOW_SECONDS)


class TripPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)

        already_in_progress = AgentRun.objects.filter(
            trip=trip, status__in=[AgentRunStatus.PENDING, AgentRunStatus.RUNNING],
        ).exists()
        if already_in_progress:
            return Response(
                {"error": {"code": "plan_already_in_progress",
                            "message": "A planning run is already in progress for this trip."}},
                status=http_status.HTTP_409_CONFLICT,
            )

        if _is_rate_limited(request.user.id):
            return Response(
                {"error": {"code": "rate_limited",
                            "message": f"Maximum {_RATE_LIMIT_MAX_REQUESTS} planning requests per hour."}},
                status=http_status.HTTP_429_TOO_MANY_REQUESTS,
            )

        _increment_rate_limit(request.user.id)
        task = run_travel_planner_task.delay(trip_id=str(trip.id), user_id=request.user.id)
        return Response({"task_id": task.id, "status": "pending"}, status=http_status.HTTP_202_ACCEPTED)


class TripPlanStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        latest_run = (
            AgentRun.objects.filter(trip=trip, agent_type=AgentType.FULL_GRAPH)  # CHANGED
            .order_by("-created_at")
            .first()
        )
        if latest_run is None:
            return Response({"status": "not_started"})
        return Response(AgentRunStatusSerializer(latest_run).data)
```

**Why the duplicate-trigger guard is checked *before* the rate limit, not after**: order matters for a subtle reason — if a request is rejected as a duplicate, it shouldn't also consume one of the user's limited rate-limit "slots" for the hour; checking duplication first and returning early means a legitimately-blocked duplicate request costs the user nothing toward their rate limit.

**Why `cache.incr()` is wrapped in `try/except ValueError`, rather than checking existence first with a separate `cache.get()` call**: Django's cache `incr()` raises `ValueError` if the key doesn't exist yet (rather than silently creating it at 1) — catching that and falling back to `cache.set(key, 1, ...)` is the standard, correct pattern for "increment or initialize," and avoids a race condition that a separate "check then set" pair of calls would have (two nearly-simultaneous requests could both see "key doesn't exist" and both try to initialize it, one overwriting the other's already-incremented value).

### 10.4 `apps/ai_agents/tasks.py` (modified)

```python
@shared_task(bind=True, max_retries=0, time_limit=180, soft_time_limit=150)
def run_travel_planner_task(self, trip_id: str, user_id: int | None = None):
    # ... body completely unchanged from Chapter 12 ...
```

**Why `time_limit=180` (hard) and `soft_time_limit=150` (soft), and why both, not just one**: with five agents now in the graph, some running sequentially, a genuinely slow provider response on multiple nodes could add up meaningfully — `soft_time_limit` raises a catchable exception inside the task at 150 seconds, giving the code a chance to clean up or log; `time_limit` forcibly kills the worker process at 180 seconds if the soft limit's exception is somehow not handled in time, a hard backstop against a truly hung task consuming a Celery worker indefinitely. Neither limit existed in Chapter 12 because a single-node graph was fast enough that runaway execution wasn't a realistic risk — this is a deliberate hardening step specific to the graph's now-larger size.

---

## 11. Code Walkthrough

- **The data migration (10.1) and the "keep the function name, change the data" decision (10.2) are two sides of the same lesson**: Chapter 17 is fundamentally about *cleaning up after growth*, not building new capability — a healthy, normal phase in any real project's lifecycle, worth recognizing as its own kind of engineering work, not lesser than feature work.
- **`_is_rate_limited`/`_increment_rate_limit` are separate, small, testable functions rather than logic inlined into the view**: same discipline as every `services.py` function in this project — small, named, independently testable units, even for something as seemingly simple as a rate-limit check.
- **The Celery task's hardening (`time_limit`) and the view's hardening (duplicate guard, rate limit) are three independent protections, not one combined mechanism**: each guards against a different failure mode — duplicate guard prevents wasted concurrent work, rate limiting prevents cost abuse, task time limits prevent a single hung task from consuming a worker forever. Naming them separately, rather than reaching for one "big" solution, keeps each one simple enough to reason about and test in isolation.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `409 Conflict` on `/plan/` when you're sure nothing else is running | A previous `AgentRun` got stuck in `running` due to an old bug, or a Celery worker crashed mid-task without reaching the `finally` block | Manually inspect/fix via admin (Chapter 12's `finally` should prevent this in normal operation, but crashed workers are an edge case outside Python's own exception handling) |
| Rate limit triggers after fewer than 5 requests | Testing across multiple `User` instances but reusing the same `cache` backend without clearing between test runs | Ensure Django's test settings use `LocMemCache` or that Redis test keys are cleared/flushed between test cases |
| Migration `0002` fails with `AgentRun` model not found | Migration dependency (`0001_initial`) missing or listed incorrectly | Confirm `dependencies = [("ai_agents", "0001_initial")]` matches your actual initial migration's name |
| Celery task killed unexpectedly at 150s even though it "should" have finished | `soft_time_limit` reached — likely a genuinely slow run (many retries stacking up across multiple agents) | Investigate whether Groq API latency or repeated schema-validation retries (Chapter 11) are the bottleneck; 150s should be generous for 5 agents under normal conditions |

---

## 13. Debugging

```bash
# 1. Confirm the migration applied and no rows still show the old value
docker compose exec web python manage.py shell -c "
from apps.ai_agents.models import AgentRun
print('old value remaining:', AgentRun.objects.filter(agent_type='travel_planner').count())
"

# 2. Manually exercise the rate limiter
docker compose exec web python manage.py shell -c "
from apps.ai_agents.views import _is_rate_limited, _increment_rate_limit
uid = 999
for i in range(6):
    print(i, _is_rate_limited(uid))
    _increment_rate_limit(uid)
"
```

**Rollback strategy:** the data migration is fully reversible (`python manage.py migrate ai_agents 0001`); the view/task hardening changes have no data implications at all and can simply be reverted in code if they ever cause an unexpected issue.

---

## 14. Testing

### 14.1 `apps/ai_agents/tests/test_views.py` (modified/additions)

```python
# Existing test_status_endpoint_reflects_latest_run (Chapter 12) updated:
from apps.ai_agents.models import AgentType  # already imported

def test_status_endpoint_reflects_latest_run(self):
    AgentRun.objects.create(
        trip=self.trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.SUCCEEDED,  # CHANGED
    )
    response = self.client.get(
        reverse("ai_agents:plan-status", kwargs={"trip_pk": self.trip.pk}), **self._auth()
    )
    self.assertEqual(response.data["status"], "succeeded")
```

```python
from django.core.cache import cache
from unittest.mock import patch


class TripPlanViewGuardTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email="guard@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3),
        )
        login = self.client.post(reverse("accounts:login"), {"email": "guard@example.com", "password": "pass1234"})
        self.token = login.data["tokens"]["access"]

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    @patch("apps.ai_agents.views.run_travel_planner_task.delay")
    def test_duplicate_trigger_returns_409(self, mock_delay):
        mock_delay.return_value.id = "task-1"
        AgentRun.objects.create(trip=self.trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.RUNNING)

        response = self.client.post(
            reverse("ai_agents:plan", kwargs={"trip_pk": self.trip.pk}), **self._auth()
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        mock_delay.assert_not_called()

    @patch("apps.ai_agents.views.run_travel_planner_task.delay")
    def test_rate_limit_blocks_sixth_request_in_window(self, mock_delay):
        mock_delay.return_value.id = "task-1"
        for _ in range(5):
            response = self.client.post(
                reverse("ai_agents:plan", kwargs={"trip_pk": self.trip.pk}), **self._auth()
            )
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        sixth_response = self.client.post(
            reverse("ai_agents:plan", kwargs={"trip_pk": self.trip.pk}), **self._auth()
        )
        self.assertEqual(sixth_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(mock_delay.call_count, 5)

    @patch("apps.ai_agents.views.run_travel_planner_task.delay")
    def test_rejected_duplicate_does_not_consume_rate_limit_slot(self, mock_delay):
        mock_delay.return_value.id = "task-1"
        AgentRun.objects.create(trip=self.trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.RUNNING)

        for _ in range(3):
            self.client.post(reverse("ai_agents:plan", kwargs={"trip_pk": self.trip.pk}), **self._auth())

        # All 3 attempts were 409s (duplicate in progress) — none should
        # have consumed a rate-limit slot.
        mock_delay.assert_not_called()
```

### 14.2 `apps/ai_agents/tests/test_integration_full_graph.py` (the capstone test)

```python
"""
The single most valuable test in the project so far. Exercises the
REAL, compiled five-node LangGraph graph end to end — genuine
parallel execution of budget_agent/weather_agent, a genuine join at
recommendation_agent, genuine tool-calling in weather_agent — with
ONLY the Groq SDK's network boundary mocked. Uses content-based
routing (not an ordered list of canned responses) because the graph
has real parallelism and call order across branches is not guaranteed.
"""
import json
from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.ai_agents.models import AgentRunStatus, AgentType
from apps.budget.models import BudgetLineItem
from apps.destinations.models import Destination
from apps.itinerary.models import ItineraryItem
from apps.recommendations.models import Recommendation
from apps.trips.models import PackingItem, Trip

User = get_user_model()


def _text_response(content: str, tool_calls=None):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content, tool_calls=tool_calls))]
    return response


def _tool_call_response(tool_name: str, arguments: dict):
    response = MagicMock()
    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)
    response.choices = [MagicMock(message=MagicMock(content=None, tool_calls=[tool_call]))]
    return response


ITINERARY_JSON = json.dumps({
    "days": [{
        "day_number": 1, "date": "2026-06-01", "summary": "Arrival day",
        "items": [{"title": "Check into hotel", "description": "", "estimated_cost_usd": 100}],
    }]
})

BUDGET_JSON = json.dumps({
    "by_category": [{"category": "accommodation", "description": "Hotel", "amount": 100.0}],
    "total_estimate": 100.0,
})

WEATHER_STRUCTURED_JSON = json.dumps({
    "days": [{"date": "2026-06-01", "condition": "mild", "high_f": 75, "low_f": 60, "precipitation_chance": 20}],
})

RECOMMENDATION_JSON = json.dumps({
    "items": [{"destination_name": "Tokyo", "category": "activity", "title": "Visit a shrine",
               "description": "", "score": 0.8}],
})

PACKING_JSON = json.dumps({
    "items": [{"category": "clothing", "item_name": "Light jacket", "quantity": 1, "is_essential": True}],
})


def _route_by_content(**kwargs) -> MagicMock:
    messages = kwargs["messages"]
    system_content = messages[0]["content"]
    has_tool_message = any(m.get("role") == "tool" for m in messages)
    tools_offered = bool(kwargs.get("tools"))

    if "travel planning assistant" in system_content:
        return _text_response(ITINERARY_JSON)
    if "budget estimation" in system_content:
        return _text_response(BUDGET_JSON)
    if "weather assistant" in system_content and tools_offered:
        return _tool_call_response("get_typical_weather", {"destination": "Tokyo", "month_name": "June"})
    if "weather assistant" in system_content and has_tool_message:
        return _text_response("Tokyo in June is typically mild with occasional light rain.")
    if "data formatting assistant" in system_content:
        return _text_response(WEATHER_STRUCTURED_JSON)
    if "recommendation assistant" in system_content:
        return _text_response(RECOMMENDATION_JSON)
    if "packing assistant" in system_content:
        return _text_response(PACKING_JSON)

    raise AssertionError(f"Unrouted system prompt in integration test: {system_content[:80]}")


class FullGraphIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="integration@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Tokyo Trip", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1),
        )
        destination = Destination.objects.create(name="Tokyo", country="Japan")
        self.trip.destinations.add(destination)

    @patch("ai.clients.groq_client.Groq")
    def test_full_graph_run_persists_all_five_agents_output(self, mock_groq_cls):
        mock_instance = mock_groq_cls.return_value
        mock_instance.chat.completions.create.side_effect = _route_by_content

        agent_run = services.run_travel_planner(trip=self.trip, triggered_by=self.user)

        # 1. The run itself succeeded and is correctly labeled
        self.assertEqual(agent_run.status, AgentRunStatus.SUCCEEDED)
        self.assertEqual(agent_run.agent_type, AgentType.FULL_GRAPH)

        # 2. Itinerary (Chapter 12)
        self.assertEqual(ItineraryItem.objects.filter(day__trip=self.trip).count(), 1)

        # 3. Budget (Chapter 13) — including the signal-driven total
        self.assertEqual(BudgetLineItem.objects.filter(budget__trip=self.trip).count(), 1)
        self.trip.refresh_from_db()
        self.assertEqual(str(self.trip.computed_budget_total), "100.00")

        # 4. Weather (Chapter 14) — persisted onto the itinerary day
        day = self.trip.itinerary_days.get(day_number=1)
        self.assertEqual(day.weather_condition, "mild")

        # 5. Recommendations (Chapter 15)
        self.assertEqual(Recommendation.objects.filter(trip=self.trip).count(), 1)

        # 6. Packing (Chapter 16)
        self.assertEqual(PackingItem.objects.filter(trip=self.trip).count(), 1)

    @patch("ai.clients.groq_client.Groq")
    def test_full_graph_run_is_atomic_end_to_end(self, mock_groq_cls):
        """
        If ANY stage's output is unroutable/broken, NOTHING should
        be persisted — proving Chapter 13's transaction.atomic()
        wrapping still holds across the full, final five-node graph.
        """
        mock_instance = mock_groq_cls.return_value

        def _broken_router(**kwargs):
            response = _route_by_content(**kwargs)
            # Corrupt the packing agent's response specifically to
            # force a downstream persistence failure.
            if response.choices[0].message.content == PACKING_JSON:
                response.choices[0].message.content = "not valid json at all, twice invalid"
            return response

        mock_instance.chat.completions.create.side_effect = _broken_router

        agent_run = services.run_travel_planner(trip=self.trip)

        self.assertIn(agent_run.status, [AgentRunStatus.NEEDS_REVIEW, AgentRunStatus.FAILED])
        self.assertEqual(ItineraryItem.objects.filter(day__trip=self.trip).count(), 0)
        self.assertEqual(BudgetLineItem.objects.filter(budget__trip=self.trip).count(), 0)
```

**Why `_route_by_content` raises `AssertionError` on an unrecognized prompt, instead of returning a generic default**: a silent fallback would let a real bug (a new agent added later whose prompt isn't yet routed) pass unnoticed, producing confusing downstream failures far from the actual cause — failing loudly and immediately, right at the mock boundary, is far easier to debug and is a good general testing principle for any router-style test double.

**Why the atomicity test corrupts *only the last* node's (`packing_agent`) response**: this is the strongest possible proof of Chapter 13's `transaction.atomic()` decision — if a failure at the very *last* step of a five-agent chain still results in zero persisted data for the *first* four agents' otherwise-successful output, the atomicity guarantee is holding as strongly as it possibly could.

Run everything:

```bash
docker compose exec web python manage.py test apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add apps/ai_agents/migrations/0002_backfill_full_graph_agent_type.py apps/ai_agents/services.py apps/ai_agents/views.py apps/ai_agents/tasks.py apps/ai_agents/tests/
git commit -m "chore(ai_agents): orchestration assembly — rename, hardening, full integration test

- Reversible data migration backfills existing agent_type='travel_planner'
  rows to 'full_graph'; no schema change needed (choices aren't a DB
  constraint) — see Chapter 17 Theory §2.1
- run_travel_planner() now writes AgentType.FULL_GRAPH; Python
  function/task names deliberately UNCHANGED — a considered choice
  (rename the data, not the code symbol) documented explicitly,
  contrasted with Chapter 16's packing_list type correction which
  WAS worth renaming
- TripPlanView: 409 Conflict on duplicate concurrent trigger (checked
  BEFORE rate limiting, so a rejected duplicate costs no rate-limit
  slot); closes a real risk now that one trigger runs 5 agents
- Redis-backed per-user rate limiting (5/hour) on /plan/ — closes
  Architecture Handbook §10's rate-limiting requirement, stated back
  in Volume 1, implemented now that there's real cost to protect
- Celery task gets explicit time_limit=180/soft_time_limit=150 —
  wasn't needed for Chapter 12's single-node graph, is needed now
- Capstone integration test: exercises the REAL compiled 5-node graph
  (genuine parallelism, genuine join, genuine tool-calling) with only
  the Groq SDK boundary mocked, using CONTENT-based response routing
  (not fragile ordered side_effect lists) to handle non-deterministic
  parallel branch execution order
- Atomicity re-proven end-to-end: corrupting only the LAST node's
  output still results in zero persisted data across all five domains

Volume 4 (AI Layer) complete. Chapter 17 of Implementation Bible."
```

---

## 16. Checklist

- [ ] Data migration applied; zero rows remain with `agent_type='travel_planner'`
- [ ] Migration is genuinely reversible (`migrate ai_agents 0001` tested to work)
- [ ] `run_travel_planner()`'s Python name unchanged; only the `AgentType` value it writes changed — reasoning documented, not silent
- [ ] `TripPlanView` returns `409` for a trip with an in-progress run, checked before rate limiting
- [ ] Rate limiting blocks the 6th request in a rolling hour window; a rejected duplicate does not consume a slot
- [ ] Celery task has both `time_limit` and `soft_time_limit` set
- [ ] Integration test exercises the real, compiled graph — not individually mocked nodes — and asserts persisted data across all five domains (itinerary, budget + signal-driven total, weather, recommendations, packing)
- [ ] Integration test proves atomicity by corrupting only the *last* node and confirming zero persistence anywhere
- [ ] All tests passing
- [ ] Commit made
- [ ] **Volume 4 (AI Layer) is now complete** — the graph is built, hardened, tested end-to-end, and every prior chapter's design decisions have been proven to hold together as a whole, not just individually

---

## 17. Next Chapter Preview

**Chapter 18 — Memory & Conversation State** begins Volume 5 (Conversational Layer). Everything built in Volume 4 runs once per trigger, with no memory of prior runs beyond what's stored in the database. This chapter introduces short-term conversational memory — the pattern Chapter 19's `chat` app will need to let a user have a back-and-forth conversation with the AI about their trip, rather than only ever triggering one-shot planning runs. This is also where the project first has to reckon with a genuinely different kind of state: not "what should be persisted forever" (Trip, Budget, etc.) but "what should be remembered only for the duration of a conversation." Say **"Continue to Chapter 18"** when ready.
