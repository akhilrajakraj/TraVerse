# Chapter 13 — Budget Agent

**Volume 4: AI Layer | Chapter 13 of 29**

> This chapter adds the second node to the planning graph built in Chapter 12: `travel_planner → budget_agent → END`. The Budget Agent reads the itinerary the Travel Planner just produced (still sitting in the shared LangGraph state) and estimates a cost for it, writing into Chapter 9's `Budget`/`BudgetLineItem` models. This is also the first agent whose output is purely numeric rather than free-form text, and the first chapter to confront Chapter 9's documented signal gap head-on, now that an AI agent is about to write line items programmatically.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Extend an existing LangGraph graph with a second, sequentially-dependent node, and understand why sequencing (not parallelism) is correct here specifically.
- Design a numeric-output Pydantic schema with cross-field validation (category subtotals that must sum to a stated total).
- Deliberately avoid Django's bulk write operations when writing AI-generated data, directly resolving the signal-bypass gap flagged in Chapter 9.
- Wrap a multi-model persistence operation (itinerary + budget) in a single database transaction, and explain why partial persistence would be worse than an outright failure.

---

## 2. Theory

### 2.1 Why the Budget Agent Must Run *After* the Travel Planner, Not in Parallel (ELI10)

Imagine asking someone to estimate the cost of a vacation before telling them where you're going or what you'll do there — they'd have nothing real to work from. The Budget Agent's entire job is to look at the *actual* itinerary (specific activities, specific estimated costs already sketched by the Travel Planner in Chapter 12's `ItineraryItemSchema.estimated_cost_usd`) and turn that into a structured, categorized budget. This is a genuine data dependency, not an arbitrary ordering choice — which is exactly why Architecture Handbook §9.2's diagram shows Budget and Weather running in parallel with *each other*, but both strictly *after* the Travel Planner. This chapter builds the `travel_planner → budget_agent` edge; Chapter 14 will add Weather as a second branch off the Travel Planner, not off the Budget Agent.

### 2.2 Why This Chapter Finally Confronts Chapter 9's Signal Gap

Chapter 9 flagged, in its own words, a "known gap": `QuerySet.update()`, `bulk_create()`, and `bulk_update()` bypass Django's `post_save`/`post_delete` signals entirely, meaning `Trip.computed_budget_total` would silently go stale if any code path used them on `BudgetLineItem`. This chapter is the first place an AI agent writes *multiple* `BudgetLineItem` rows in one operation — precisely the scenario where a well-intentioned engineer, trying to be efficient, might reach for `bulk_create()` for a "quick win" on performance. This chapter makes the opposite choice, deliberately and visibly, and explains exactly why.

### 2.3 Why Cross-Field Validation (Subtotals Summing to a Total) Belongs in the Schema, Not Just the Prompt

Telling the LLM in the prompt "make sure your category subtotals add up to the total" is a request, not a guarantee — language models are not calculators, and asking nicely doesn't make arithmetic reliable. Pydantic's `model_validator` lets us **check** the arithmetic after the fact, in code, and reject (triggering Chapter 11's retry-with-correction flow) if it's wrong — the same defense-in-depth instinct already applied to Chapter 7's date range and Chapter 9's non-negative amounts, applied here to arithmetic consistency instead.

---

## 3. Architecture Decision

**Decision:** `_persist_budget_estimate` clears previous AI-estimated line items via `budget.line_items.filter(is_ai_estimated=True).delete()` (a `QuerySet.delete()`, which **does** fire `post_delete` per row — confirmed explicitly in Section 11), then creates new ones one at a time via Chapter 9's `services.add_line_item()`, never `bulk_create()`.

**Why this is correct, not merely cautious:** `QuerySet.delete()` and `QuerySet.update()` are often lumped together as "bulk operations," but they behave differently — Django's own documentation confirms `.delete()` sends `pre_delete`/`post_delete` for each object being deleted, while `.update()` sends nothing at all. This chapter relies on that specific, real distinction rather than avoiding all queryset-level operations out of blanket caution.

**Decision:** `run_travel_planner` (Chapter 12) now persists both itinerary and budget results inside a single `transaction.atomic()` block.

**Alternative considered:** Persist itinerary and budget independently, allowing one to succeed even if the other fails. **Rejected because:** a `Trip` with a fresh AI-generated itinerary but no corresponding budget (or vice versa) is a genuinely confusing, inconsistent state to show a user — Architecture Handbook §9.8's fallback strategy ("mark `AgentRun` as `needs_review`") is about the *whole* planning attempt, not a partial one; atomicity means a failure anywhere in persistence leaves the trip's itinerary/budget exactly as they were before the run, not half-updated.

**Decision:** `BudgetEstimateSchema` validates that `by_category` subtotals sum to `total_estimate` within a small tolerance (`0.01`, to allow for floating-point/rounding noise), not an exact equality check.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Extend `ai/agents/schemas.py` with `BudgetEstimateSchema` | Needed before the prompt or node can describe the target shape |
| Write `ai/prompts/budget_agent_v1.py` | Needed before the node function |
| Write `ai/agents/budget_agent.py` (the node) | Needed before it can be added to the graph |
| Add the node + edge to `ai/graphs/planning_graph.py` | Needed before `ai_agents` sees any `budget_estimate` in the final state |
| Extend `apps/ai_agents/services.py` with `_persist_budget_estimate` and the `transaction.atomic()` wrapper | Last — depends on everything above already producing correct data to persist |

---

## 5. File Structure

```
ai/
├── agents/
│   ├── schemas.py               # MODIFIED — adds BudgetLineItemEstimateSchema, BudgetEstimateSchema
│   └── budget_agent.py            # NEW — the second node
├── prompts/
│   └── budget_agent_v1.py          # NEW
└── graphs/
    └── planning_graph.py            # MODIFIED — adds the budget_agent node + edge

apps/ai_agents/
├── services.py                   # MODIFIED — _persist_budget_estimate, transaction.atomic() wrapper
└── tests/
    └── test_services.py            # MODIFIED — new tests for budget persistence + atomicity

ai/tests/
├── test_budget_agent.py           # NEW
└── test_planning_graph.py          # MODIFIED — asserts both nodes present
```

---

## 6. Folder Location

Modifications to existing files under `ai/` and `apps/ai_agents/`; two genuinely new files (`ai/agents/budget_agent.py`, `ai/prompts/budget_agent_v1.py`).

---

## 7. Terminal Commands

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents -v 2
```

No new migrations this chapter — `Budget`/`BudgetLineItem` (Chapter 9) and `AgentRun` (Chapter 12) already have every field this chapter needs.

---

## 8. Docker Commands

```bash
docker compose restart web celery
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py shell -c "
from apps.ai_agents import services
from apps.trips.models import Trip
trip = Trip.objects.first()
run = services.run_travel_planner(trip=trip)
trip.refresh_from_db()
print(run.status, trip.computed_budget_total)
"
succeeded 845.00
```

---

## 10. Code

### 10.1 `ai/agents/schemas.py` (addition)

```python
"""
(appended to the schemas.py file from Chapter 12)
"""
from pydantic import model_validator


class BudgetLineItemEstimateSchema(BaseModel):
    category: str = Field(..., pattern="^(accommodation|transport|food|activities|shopping|misc)$")
    description: str = Field(..., max_length=200)
    amount: float = Field(..., ge=0)


class BudgetEstimateSchema(BaseModel):
    by_category: list[BudgetLineItemEstimateSchema] = Field(..., min_length=1)
    total_estimate: float = Field(..., ge=0)

    @model_validator(mode="after")
    def subtotals_must_sum_to_total(self) -> "BudgetEstimateSchema":
        computed_total = sum(item.amount for item in self.by_category)
        if abs(computed_total - self.total_estimate) > 0.01:
            raise ValueError(
                f"by_category amounts sum to {computed_total}, "
                f"but total_estimate is {self.total_estimate}."
            )
        return self
```

**Why `category` uses a `pattern` regex instead of importing `apps.budget.models.BudgetCategory`**: importing a Django model's `TextChoices` directly into `ai/` would violate Chapter 11's zero-Django-dependency boundary — the valid category strings are duplicated here as a literal pattern instead, a small, deliberate, documented cost of maintaining the boundary (if `BudgetCategory` ever gains a new choice, this pattern must be updated too; flagged here so it isn't a silent trap).

**Why `subtotals_must_sum_to_total` is a `model_validator(mode="after")`, not a `field_validator`**: this check genuinely needs *both* fields (`by_category` and `total_estimate`) at once — Pydantic's `field_validator` only sees one field in isolation, while `model_validator(mode="after")` runs once the whole model is otherwise valid, exactly the right tool for a cross-field consistency check like this.

### 10.2 `ai/prompts/budget_agent_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a travel budget estimation assistant.
Given a day-by-day itinerary and the traveler's budget style, produce
a categorized cost estimate.

Rules:
- Respond with ONLY valid JSON matching the provided schema.
- Categories must be exactly one of: accommodation, transport, food,
  activities, shopping, misc.
- The sum of all by_category amounts MUST exactly equal total_estimate.
- Base estimates on the actual itinerary provided, not generic averages.
- Adjust overall spending level to match the stated budget style
  (shoestring = minimal spend, luxury = generous spend)."""


class BudgetAgentPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="budget_agent", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(self, *, itinerary_summary: str, budget_style: str) -> str:
        return (
            f"Traveler budget style: {budget_style}\n\n"
            f"Itinerary:\n{itinerary_summary}\n\n"
            f"Produce a categorized budget estimate for this entire trip."
        )
```

### 10.3 `ai/agents/budget_agent.py`

```python
"""
The second node in the planning graph. Depends on itinerary_plan
already being present in state — see Chapter 13 Theory §2.1 for why
this is a genuine data dependency, not an arbitrary ordering choice.
"""
from ai.agents.schemas import BudgetEstimateSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import TripPlanningState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.budget_agent_v1 import BudgetAgentPromptV1

_prompt = BudgetAgentPromptV1()


def _summarize_itinerary_for_prompt(itinerary_plan) -> str:
    lines = []
    for day in itinerary_plan.days:
        lines.append(f"Day {day.day_number} ({day.date}): {day.summary}")
        for item in day.items:
            cost_note = f" (~${item.estimated_cost_usd})" if item.estimated_cost_usd else ""
            lines.append(f"  - {item.title}{cost_note}")
    return "\n".join(lines)


def budget_agent_node(state: TripPlanningState, *, client: GroqClient | None = None) -> dict:
    client = client or GroqClient()

    itinerary_summary = _summarize_itinerary_for_prompt(state["itinerary_plan"])
    user_prompt = _prompt.render_user_prompt(
        itinerary_summary=itinerary_summary, budget_style=state["budget_style"],
    )

    estimate: BudgetEstimateSchema = parse_structured_output(
        client=client,
        system_prompt=_prompt.system_prompt,
        user_prompt=user_prompt,
        schema=BudgetEstimateSchema,
        temperature=0.2,
    )

    return {"budget_estimate": estimate.model_dump()}
```

**Why `budget_estimate` is stored in state as a plain `dict` (`.model_dump()`) rather than the `BudgetEstimateSchema` object itself, unlike `itinerary_plan` which stays a schema object**: this matches the type Chapter 12 already declared in `TripPlanningState` (`budget_estimate: dict | None`), a deliberate inconsistency explained back in that chapter — `itinerary_plan` needed to stay a rich schema object because `_persist_itinerary_plan` (Chapter 12) iterates its nested structure extensively; `budget_estimate`'s consumer (this chapter's persistence function) only needs simple key access, so a plain dict is sufficient and was sized that way from the start.

**Why `temperature=0.2`, lower even than the Travel Planner's `0.4`**: numeric/arithmetic output benefits even more from low temperature than descriptive text does — Section 2.3's cross-field validator will catch genuine arithmetic mistakes regardless, but a lower temperature reduces how often that retry path needs to trigger in the first place, the same reasoning Chapter 11 gave for its own `0.3` default.

### 10.4 `ai/graphs/planning_graph.py` (modified)

```python
"""
The trip planning graph. This chapter: TWO nodes.
travel_planner -> budget_agent -> END.
"""
from langgraph.graph import END, START, StateGraph

from ai.agents.budget_agent import budget_agent_node
from ai.agents.travel_planner import travel_planner_node
from ai.graphs.state import TripPlanningState


def build_planning_graph():
    graph = StateGraph(TripPlanningState)
    graph.add_node("travel_planner", travel_planner_node)
    graph.add_node("budget_agent", budget_agent_node)

    graph.add_edge(START, "travel_planner")
    graph.add_edge("travel_planner", "budget_agent")
    graph.add_edge("budget_agent", END)

    return graph.compile()


def run_planning_graph(initial_state: TripPlanningState) -> TripPlanningState:
    compiled_graph = build_planning_graph()
    return compiled_graph.invoke(initial_state)
```

**Why this diff is small — only three new lines beyond the new node registration**: this is the direct payoff of Chapter 12's decision to split `build_planning_graph()`/`run_planning_graph()` and to size `TripPlanningState` ahead of need — extending the graph required no changes to `run_planning_graph()`, no changes to `TripPlanningState`, and no changes to `ai_agents/services.py`'s call site (`run_planning_graph(initial_state)` is called exactly the same way it was in Chapter 12).

### 10.5 `apps/ai_agents/services.py` (modified)

```python
"""
(services.py from Chapter 12, extended)
"""
from django.db import transaction
from django.utils import timezone

from ai.exceptions import LLMCallFailed, StructuredOutputInvalid
from ai.graphs.planning_graph import run_planning_graph
from apps.ai_agents.models import AgentRun, AgentType, AgentRunStatus
from apps.budget import services as budget_services
from apps.itinerary import services as itinerary_services
from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip

logger = __import__("logging").getLogger("apps.ai_agents")


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
    for day_schema in plan.days:
        day, _ = ItineraryDay.objects.update_or_create(
            trip=trip, day_number=day_schema.day_number,
            defaults={"date": day_schema.date, "summary": day_schema.summary},
        )
        day.items.all().delete()
        for item_schema in day_schema.items:
            itinerary_services.add_item_to_day(
                day=day, title=item_schema.title, description=item_schema.description,
                start_time=item_schema.start_time, estimated_cost_usd=item_schema.estimated_cost_usd,
                is_ai_generated=True,
            )


def _persist_budget_estimate(*, trip: Trip, estimate: dict) -> None:
    """
    Deliberately uses budget_services.add_line_item() in a loop, NOT
    bulk_create() — see Chapter 13 Architecture Decision. This
    guarantees post_save fires per row, keeping
    Trip.computed_budget_total (Chapter 9's signal) correctly in
    sync with zero extra reconciliation work.
    """
    budget = trip.budget

    # QuerySet.delete() DOES fire post_delete per row (confirmed in
    # Chapter 13 Section 11) — safe to use here, unlike .update()/
    # bulk_create()/bulk_update(), which do NOT fire signals.
    budget.line_items.filter(is_ai_estimated=True).delete()

    for line in estimate["by_category"]:
        budget_services.add_line_item(
            budget=budget, category=line["category"], description=line["description"],
            amount=line["amount"], is_ai_estimated=True,
        )


def run_travel_planner(*, trip: Trip, triggered_by=None) -> AgentRun:
    initial_state = _build_initial_state(trip)
    agent_run = AgentRun.objects.create(
        trip=trip, triggered_by=triggered_by, agent_type=AgentType.TRAVEL_PLANNER,
        status=AgentRunStatus.RUNNING, input_snapshot=initial_state, started_at=timezone.now(),
    )

    try:
        final_state = run_planning_graph(initial_state)
        with transaction.atomic():
            _persist_itinerary_plan(trip=trip, plan=final_state["itinerary_plan"])
            if final_state.get("budget_estimate"):
                _persist_budget_estimate(trip=trip, estimate=final_state["budget_estimate"])
    except StructuredOutputInvalid as exc:
        logger.warning("Planning run needs review for trip %s: %s", trip.id, exc)
        agent_run.status = AgentRunStatus.NEEDS_REVIEW
        agent_run.error_message = str(exc)
    except LLMCallFailed as exc:
        logger.error("Planning run failed for trip %s: %s", trip.id, exc)
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(exc)
    else:
        agent_run.status = AgentRunStatus.SUCCEEDED
    finally:
        agent_run.completed_at = timezone.now()
        agent_run.save(update_fields=["status", "error_message", "completed_at"])

    return agent_run
```

**Why `_persist_itinerary_plan` and `_persist_budget_estimate` are both called *inside* one `with transaction.atomic():` block, rather than each function managing its own transaction**: if `_persist_budget_estimate` were to raise partway through (say, on its third line item), Django's transaction rollback undoes **everything** inside the `atomic()` block — including the itinerary rewrite that already "succeeded" moments earlier — leaving the trip's data exactly as it was before this run started, never half-updated. This is the concrete mechanism behind this chapter's Architecture Decision.

**Why `AgentRun.agent_type` stays `AgentType.TRAVEL_PLANNER` even though this single run now produces both itinerary and budget**: this is a deliberately deferred rename, called out explicitly rather than silently left inconsistent — Chapter 12 already reserved `AgentType.FULL_GRAPH` for exactly this situation, but renaming the *currently working, tested* `TRAVEL_PLANNER` label now, only two chapters after it shipped, would be premature churn before the graph reaches its actual final shape (Chapter 17, five nodes). The rename happens once, in Chapter 17, when the graph is genuinely complete — not incrementally with each new node.

---

## 11. Code Walkthrough

- **The Django signal-safety claim in this chapter (`QuerySet.delete()` fires `post_delete` per row) is not just asserted — it's proven in Section 14's tests** by creating AI-estimated line items, deleting them via the queryset filter used in `_persist_budget_estimate`, and asserting `Trip.computed_budget_total` correctly drops back to reflect only the remaining (non-AI) line items. A claim about Django signal behavior is exactly the kind of thing worth testing rather than trusting from memory or documentation alone.
- **`_summarize_itinerary_for_prompt` converts a Pydantic schema object back into a plain string for the *next* agent's prompt**: this is worth noticing as a pattern — Chapter 12's Travel Planner output (`itinerary_plan`, a rich schema) becomes Chapter 13's Budget Agent *input* (as a flattened string), because prompts are always plain text, regardless of how structured the upstream data is. Every future agent that consumes another agent's output (Chapter 15's Recommendation Agent consuming both itinerary and weather) will need its own similar flattening function.
- **User-added budget line items (`is_ai_estimated=False`, from Chapter 9's manual API) are never touched by `_persist_budget_estimate`**: the `filter(is_ai_estimated=True)` scoping on the clearing step is what makes AI regeneration and manual user edits coexist safely — exactly the reason `is_ai_estimated` was added back in Chapter 9, now finally exercised for real.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `pydantic.ValidationError: subtotals ... but total_estimate is ...` (wrapped in `StructuredOutputInvalid` after retry) | The model's arithmetic didn't add up, even after one correction attempt | Expected occasional occurrence — this is Chapter 11's retry flow and Chapter 13's cross-field validator working exactly as designed, not a bug to "fix" by loosening the tolerance |
| `KeyError: 'itinerary_plan'` inside `budget_agent_node` | `budget_agent_node` was invoked directly with a state missing `itinerary_plan` — i.e., graph edges were bypassed | Confirm the graph's edges route through `travel_planner` before `budget_agent`; never call `budget_agent_node` standalone in production code (only in isolated unit tests, where the test itself supplies a fake `itinerary_plan`) |
| `Trip.computed_budget_total` doesn't reflect newly AI-estimated line items | Someone "optimized" `_persist_budget_estimate` to use `bulk_create()` | This is exactly the regression this chapter's tests guard against — revert to the per-item `add_line_item()` loop |
| User's manually-added budget line items disappear after re-running the planner | `_persist_budget_estimate`'s delete filter was changed to remove the `is_ai_estimated=True` scoping | Restore the filter exactly as shown in 10.5 — this would be a serious data-loss bug for real users |

---

## 13. Debugging

```bash
# 1. Prove QuerySet.delete() fires signals, .update() does not — directly, not from memory
docker compose exec web python manage.py shell -c "
from apps.budget.models import BudgetLineItem
from apps.trips.models import Trip
from apps.budget import services
trip = Trip.objects.first()
item = services.add_line_item(budget=trip.budget, category='food', description='test', amount='10.00')
trip.refresh_from_db(); print('after create:', trip.computed_budget_total)

BudgetLineItem.objects.filter(pk=item.pk).delete()
trip.refresh_from_db(); print('after QuerySet.delete():', trip.computed_budget_total)
"

# 2. Run just the two-node graph in isolation with a mocked client, no real API call
docker compose exec web python manage.py shell -c "
from unittest.mock import MagicMock
from ai.graphs.planning_graph import build_planning_graph
graph = build_planning_graph()
print([n for n in graph.get_graph().nodes.keys()])
"
```

**Rollback strategy:** identical to Chapter 12's — because persistence is wrapped in `transaction.atomic()`, a failed run leaves no partial data behind at all; simply re-run `run_travel_planner` once the underlying cause (a bad prompt, a provider outage) is resolved.

---

## 14. Testing

### 14.1 `ai/tests/test_budget_agent.py`

```python
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from ai.agents.budget_agent import budget_agent_node
from ai.agents.schemas import BudgetEstimateSchema, ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema


def _fake_itinerary_plan():
    return ItineraryPlanSchema(days=[
        ItineraryDaySchema(day_number=1, date="2026-06-01", items=[
            ItineraryItemSchema(title="Hotel check-in", estimated_cost_usd=100),
        ])
    ])


def test_budget_agent_node_returns_partial_dict_update():
    fake_client = MagicMock()
    fake_client.call.return_value = (
        '{"by_category": [{"category": "accommodation", "description": "Hotel", "amount": 100.0}], '
        '"total_estimate": 100.0}'
    )

    state = {"itinerary_plan": _fake_itinerary_plan(), "budget_style": "moderate"}
    result = budget_agent_node(state, client=fake_client)

    assert "budget_estimate" in result
    assert result["budget_estimate"]["total_estimate"] == 100.0


def test_schema_rejects_mismatched_subtotals():
    with pytest.raises(ValidationError):
        BudgetEstimateSchema(
            by_category=[{"category": "food", "description": "Meals", "amount": 50.0}],
            total_estimate=999.0,
        )


def test_schema_accepts_small_floating_point_tolerance():
    # 33.33 + 33.33 + 33.34 = 100.00 exactly, but real-world floats
    # can be off by a hair — this must still pass.
    estimate = BudgetEstimateSchema(
        by_category=[
            {"category": "food", "description": "A", "amount": 33.33},
            {"category": "transport", "description": "B", "amount": 33.33},
            {"category": "misc", "description": "C", "amount": 33.34},
        ],
        total_estimate=100.00,
    )
    assert estimate.total_estimate == 100.00
```

### 14.2 `ai/tests/test_planning_graph.py` (modified)

```python
from ai.graphs.planning_graph import build_planning_graph


def test_graph_has_both_nodes():
    graph = build_planning_graph()
    node_names = set(graph.get_graph().nodes.keys())
    assert {"travel_planner", "budget_agent"}.issubset(node_names)


def test_travel_planner_runs_before_budget_agent():
    graph = build_planning_graph()
    edges = graph.get_graph().edges
    edge_pairs = {(e.source, e.target) for e in edges}
    assert ("travel_planner", "budget_agent") in edge_pairs
```

### 14.3 `apps/ai_agents/tests/test_services.py` (additions)

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.ai_agents.models import AgentRunStatus
from apps.budget.models import BudgetLineItem
from apps.budget import services as budget_services
from apps.itinerary.models import ItineraryItem
from apps.trips.models import Trip
from ai.agents.schemas import (
    BudgetEstimateSchema,
    BudgetLineItemEstimateSchema,
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
)
from ai.exceptions import StructuredOutputInvalid

User = get_user_model()


def _fake_full_state():
    return {
        "itinerary_plan": ItineraryPlanSchema(days=[
            ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                ItineraryItemSchema(title="Check in", estimated_cost_usd=100)
            ])
        ]),
        "budget_estimate": BudgetEstimateSchema(
            by_category=[
                BudgetLineItemEstimateSchema(category="accommodation", description="Hotel", amount=100.0),
                BudgetLineItemEstimateSchema(category="food", description="Meals", amount=50.0),
            ],
            total_estimate=150.0,
        ).model_dump(),
    }


class BudgetPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="budget@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3),
        )

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_budget_line_items_persisted_alongside_itinerary(self, mock_graph):
        mock_graph.return_value = _fake_full_state()

        agent_run = services.run_travel_planner(trip=self.trip)

        self.assertEqual(agent_run.status, AgentRunStatus.SUCCEEDED)
        self.assertEqual(BudgetLineItem.objects.filter(budget__trip=self.trip).count(), 2)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_trip_computed_budget_total_updates_via_signal(self, mock_graph):
        mock_graph.return_value = _fake_full_state()
        services.run_travel_planner(trip=self.trip)
        self.trip.refresh_from_db()
        self.assertEqual(str(self.trip.computed_budget_total), "150.00")

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_user_added_line_items_survive_rerun(self, mock_graph):
        budget_services.add_line_item(
            budget=self.trip.budget, category="shopping", description="Souvenirs",
            amount="25.00", is_ai_estimated=False,
        )
        mock_graph.return_value = _fake_full_state()
        services.run_travel_planner(trip=self.trip)

        line_items = BudgetLineItem.objects.filter(budget__trip=self.trip)
        self.assertTrue(line_items.filter(description="Souvenirs", is_ai_estimated=False).exists())
        self.trip.refresh_from_db()
        self.assertEqual(str(self.trip.computed_budget_total), "175.00")  # 150 AI + 25 manual

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_rerun_replaces_only_ai_estimated_items(self, mock_graph):
        mock_graph.return_value = _fake_full_state()
        services.run_travel_planner(trip=self.trip)
        self.assertEqual(BudgetLineItem.objects.filter(budget__trip=self.trip, is_ai_estimated=True).count(), 2)

        second_state = _fake_full_state()
        second_state["budget_estimate"] = BudgetEstimateSchema(
            by_category=[
                BudgetLineItemEstimateSchema(category="transport", description="Trains", amount=40.0),
            ],
            total_estimate=40.0,
        ).model_dump()
        mock_graph.return_value = second_state
        services.run_travel_planner(trip=self.trip)

        ai_items = BudgetLineItem.objects.filter(budget__trip=self.trip, is_ai_estimated=True)
        self.assertEqual(ai_items.count(), 1)
        self.assertEqual(ai_items.first().description, "Trains")

    @patch("apps.ai_agents.services._persist_budget_estimate")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_atomic_rollback_on_budget_persistence_failure(self, mock_graph, mock_persist_budget):
        # Simulate itinerary persisting fine, then budget persistence
        # blowing up — the itinerary write must be rolled back too.
        mock_graph.return_value = _fake_full_state()
        mock_persist_budget.side_effect = RuntimeError("simulated failure")

        with self.assertRaises(RuntimeError):
            services.run_travel_planner(trip=self.trip)

        self.assertEqual(ItineraryItem.objects.filter(day__trip=self.trip).count(), 0)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_structured_output_invalid_still_marks_needs_review(self, mock_graph):
        mock_graph.side_effect = StructuredOutputInvalid("bad budget math")
        agent_run = services.run_travel_planner(trip=self.trip)
        self.assertEqual(agent_run.status, AgentRunStatus.NEEDS_REVIEW)
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add ai/agents/schemas.py ai/agents/budget_agent.py ai/prompts/budget_agent_v1.py ai/graphs/planning_graph.py apps/ai_agents/services.py ai/tests/ apps/ai_agents/tests/test_services.py
git commit -m "feat(ai_agents): Budget Agent — second graph node, atomic persistence

- BudgetEstimateSchema: cross-field model_validator ensures
  by_category subtotals sum to total_estimate (0.01 float tolerance),
  catching arithmetic mistakes a prompt instruction alone cannot
  guarantee
- budget_agent_node: second node, genuine sequential dependency on
  travel_planner's itinerary_plan output (not arbitrary ordering —
  see Chapter 13 Theory)
- planning_graph.py extended with 3 new lines total (node + 2 edges)
  — direct payoff of Chapter 12's build/run split and pre-sized state
- _persist_budget_estimate deliberately uses per-item add_line_item()
  in a loop, NEVER bulk_create() — directly resolves Chapter 9's
  documented signal-bypass gap; QuerySet.delete() confirmed (and
  tested) to still fire post_delete per row, used safely for clearing
  stale AI estimates
- is_ai_estimated=True scoping on the clearing step preserves user-
  added line items across re-runs — tested explicitly
- Itinerary + budget persistence now wrapped in one transaction.atomic()
  block — a failure in budget persistence rolls back the itinerary
  write too, tested via a simulated failure
- AgentType.TRAVEL_PLANNER intentionally NOT renamed yet despite this
  run now producing budget too — deferred to Chapter 17's FULL_GRAPH
  rename by design, not oversight

Chapter 13 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `BudgetEstimateSchema`'s cross-field validator rejects mismatched subtotals, tolerates float rounding noise
- [ ] `budget_agent_node` correctly reads `itinerary_plan` from state and never runs standalone in production (graph-only)
- [ ] Graph has both nodes with the correct `travel_planner → budget_agent` edge, verified by inspecting `get_graph()`
- [ ] `_persist_budget_estimate` uses `add_line_item()` per row, never `bulk_create()` — confirmed by code inspection AND a passing signal-sync test
- [ ] `QuerySet.delete()`'s signal-firing behavior is proven by a real test, not assumed
- [ ] User-added (`is_ai_estimated=False`) line items survive a planner re-run — tested explicitly
- [ ] Itinerary + budget persistence wrapped in one `transaction.atomic()`; rollback-on-failure tested with a simulated exception
- [ ] `Trip.computed_budget_total` correctly reflects AI-estimated + manual line items together after a run
- [ ] All tests passing in both `ai/tests` and `apps.ai_agents`
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 14 — Weather Agent** adds the project's first genuine **tool-calling** agent — rather than only reasoning over text, it calls an external weather API as a tool mid-reasoning, the pattern Architecture Handbook §9.6 describes ("The LLM decides *when* to call them; our code guarantees *what* they return is validated and safe"). This is also the first agent that branches directly off the Travel Planner in parallel with the Budget Agent, rather than extending a single sequential chain — the graph's shape genuinely changes shape for the first time, not just grows longer. Say **"Continue to Chapter 14"** when ready.
