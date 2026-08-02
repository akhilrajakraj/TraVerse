# Chapter 15 — Recommendation Agent

**Volume 4: AI Layer | Chapter 15 of 29**

> The graph's first real join point. `recommendation_agent` depends on **both** parallel branches from Chapter 14 — Budget and Weather — completing before it can run, the mirror image of Chapter 14's fan-out. This chapter also finally puts Chapter 10's `Recommendation` model to work, three chapters after it was built as an empty data layer, and introduces the third — and most carefully reasoned — regeneration strategy in the project: unlike itinerary's full replace (Chapter 12) or budget's AI-only replace (Chapter 13), recommendations must preserve a user's accept/reject decisions across regeneration.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Wire a join point in LangGraph — a node with multiple incoming edges that only runs once every predecessor has completed.
- Design an agent that synthesizes **three** upstream signals (itinerary, weather, budget) into one output, and justify why budget-awareness belongs here even though Architecture Handbook §9.3 only explicitly names itinerary and weather as inputs.
- Resolve AI-generated destination *names* back into real `Destination` foreign keys, and handle the case where the model names a destination that doesn't actually match.
- Compare and explain, side by side, the three different regeneration strategies this project now has for AI-touched data (itinerary, budget, recommendations) and why each is correct for its own model.

---

## 2. Theory

### 2.1 What a "Join Point" Is (ELI10)

Chapter 14 built a fork in the road — one path splits into two (Budget, Weather). A join point is where two paths merge back into one. Picture two friends running separate errands who agreed to meet at a coffee shop before doing the next thing together — neither leaves for the coffee shop until *both* errands are done. In LangGraph, this is expressed simply: give a node **two incoming edges** (from `budget_agent` and from `weather_agent`) instead of one, and the graph runtime automatically waits for both predecessors to finish before running it — no manual "wait for both" logic needs to be written by hand.

### 2.2 Why Recommendations Should Be Budget-Aware, Beyond What Architecture Handbook §9.3 Strictly Requires

Architecture Handbook §9.3 lists the Recommendation Agent's input as "Itinerary + weather." This chapter makes a deliberate, documented extension: also feeding in the budget estimate. The reasoning is concrete — recommending a $150 tasting menu to a traveler whose `budget_style` is `shoestring` and whose budget is already tight is a genuinely bad recommendation, regardless of how well it matches the weather or itinerary. This is exactly the kind of implementation-level refinement an Architecture Decision section exists to document: not contradicting the original design, but extending it with a concrete, justified reason, made explicit rather than silently smuggled in.

### 2.3 Why Three Different Data Models Need Three Different Regeneration Strategies

- **Itinerary (Chapter 12):** full replace. There's no concept of a user "deciding" on an itinerary item the way they decide on a recommendation — editing is direct, not a judgment call to preserve.
- **Budget (Chapter 13):** replace AI-estimated items only, always preserve manually-entered ones (`is_ai_estimated=False`) — a user's real receipts must never be silently deleted by a regeneration.
- **Recommendations (this chapter):** replace only **pending** AI-generated ones. A recommendation the user already **accepted** or **rejected** represents a real decision — silently deleting an accepted "Visit Fushimi Inari Shrine" recommendation the user has already committed to, just because the agent re-ran, would be actively harmful to the user's trust in the product. Only recommendations still awaiting a decision are fair game to refresh.

Seeing these three strategies side by side is the actual lesson here: "how do I handle AI regeneration" doesn't have one universal answer — it depends on whether the data represents a *plan* (replace freely), *actuals* (never touch), or a *pending decision* (replace only what's undecided).

---

## 3. Architecture Decision

**Decision:** `recommendation_agent` has two incoming graph edges (`budget_agent → recommendation_agent`, `weather_agent → recommendation_agent`), replacing both agents' previous direct edges to `END`.

**Decision:** The agent's prompt incorporates `budget_estimate` alongside `itinerary_plan` and `weather_forecast`, extending beyond Architecture Handbook §9.3's stated two inputs, with the reasoning in Section 2.2 documented here as the justification.

**Decision:** `_persist_recommendations` only deletes recommendations matching **both** `is_ai_generated=True` **and** `status=RecommendationStatus.PENDING` before creating new ones — accepted and rejected recommendations are never touched by a re-run, under any circumstances.

**Alternative considered:** Replace all AI-generated recommendations regardless of status, matching the simpler pattern from itinerary/budget. **Rejected because:** Section 2.3 already lays out why — recommendations are the first AI-touched model in this project where the *user's decision*, not just the AI's output, is the thing worth protecting across a regeneration.

**Decision:** A recommendation whose `destination_name` doesn't match any of the trip's linked `Destination`s is **skipped**, not created with a null/guessed destination — matching Chapter 10's decision that `Recommendation.destination` is required, never nullable.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Add `apps/recommendations/services.py` creation/clearing functions | Needed before `ai_agents` can persist anything into `Recommendation` |
| Write `ai/agents/schemas.py` additions | Needed before the prompt/node can describe the target shape |
| Write `ai/prompts/recommendation_agent_v1.py` | Needed before the node |
| Write `ai/agents/recommendation_agent.py` | Needed before it can join the graph |
| Add the join edges to `planning_graph.py` | Needed before `ai_agents` sees `recommendations` in final state |
| Extend `apps/ai_agents/services.py` with `_persist_recommendations` | Last |

---

## 5. File Structure

```
apps/recommendations/
└── services.py                    # MODIFIED — adds create_recommendation, clear_pending_ai_recommendations

ai/
├── agents/
│   ├── schemas.py                   # MODIFIED — RecommendationItemSchema, RecommendationBatchSchema
│   └── recommendation_agent.py        # NEW
├── prompts/
│   └── recommendation_agent_v1.py      # NEW
└── graphs/
    └── planning_graph.py              # MODIFIED — join point replaces two direct-to-END edges

apps/ai_agents/
├── services.py                    # MODIFIED — _persist_recommendations
└── tests/test_services.py           # MODIFIED

ai/tests/
├── test_recommendation_agent.py      # NEW
└── test_planning_graph.py             # MODIFIED — asserts join structure
```

---

## 6. Folder Location

Modified/new files under `apps/recommendations/`, `ai/`, `apps/ai_agents/`. No new migrations this chapter — Chapter 10's `Recommendation` model already has every field needed.

---

## 7. Terminal Commands

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.recommendations -v 2
```

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
print(run.status, trip.recommendations.count())
"
succeeded 4
```

---

## 10. Code

### 10.1 `apps/recommendations/services.py` (addition)

```python
"""
(appended to services.py from Chapter 10)
"""
from apps.recommendations.models import Recommendation, RecommendationStatus


def create_recommendation(*, trip, destination, category: str, title: str,
                           description: str = "", score=None, is_ai_generated: bool = True) -> Recommendation:
    return Recommendation.objects.create(
        trip=trip, destination=destination, category=category, title=title,
        description=description, score=score, is_ai_generated=is_ai_generated,
    )


def clear_pending_ai_recommendations(*, trip) -> None:
    """
    Deletes only AI-generated recommendations still awaiting a
    decision. Accepted/rejected recommendations are NEVER touched
    here — see Chapter 15 Theory §2.3 for why this is a genuinely
    different regeneration strategy than itinerary or budget.
    """
    trip.recommendations.filter(
        is_ai_generated=True, status=RecommendationStatus.PENDING,
    ).delete()
```

**Why these live in `apps/recommendations/services.py`, not directly in `apps/ai_agents/services.py`**: this follows the exact same discipline already established in Chapters 12-14 — `ai_agents` orchestrates and persists, but always *through* each domain app's own service layer, never with a raw `Recommendation.objects.create()` call of its own. `ai_agents` doesn't own recommendation business rules; `recommendations` does.

### 10.2 `ai/agents/schemas.py` (addition)

```python
"""
(appended to schemas.py from Chapters 12-14)
"""


class RecommendationItemSchema(BaseModel):
    destination_name: str = Field(..., max_length=150)
    category: str = Field(..., pattern="^(activity|restaurant|accommodation|transport|event)$")
    title: str = Field(..., max_length=200)
    description: str = Field(default="", max_length=1000)
    score: float = Field(..., ge=0.0, le=1.0)


class RecommendationBatchSchema(BaseModel):
    items: list[RecommendationItemSchema] = Field(..., min_length=1, max_length=15)
```

**Why `category`'s pattern mirrors Chapter 13's approach exactly (a regex literal, not a Django import)**: consistency of technique across every schema that needs to reference a Django `TextChoices` set without importing Django — this is now the third schema (after Budget's category, Weather's bounds) to reach for the same solution to the same underlying constraint, worth recognizing as an established project convention at this point, not a one-off.

**Why `max_length=15` on `items`**: bounds the batch size the same way Chapter 12's itinerary items were bounded (1-12 per day) — an unbounded or suspiciously large recommendation batch is a signal of degenerate output, caught at the schema level rather than flooding a user's recommendations page.

### 10.3 `ai/prompts/recommendation_agent_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a travel recommendation assistant.
Given a trip's itinerary, weather outlook, and budget estimate,
suggest additional activities, restaurants, or experiences the
traveler might enjoy alongside their existing plan.

Rules:
- Respond with ONLY valid JSON matching the provided schema.
- Every recommendation's destination_name MUST exactly match one of
  the destinations listed in the trip context.
- Weather-appropriate: suggest indoor options on days with high
  precipitation chance, outdoor options on clear days.
- Budget-appropriate: do not suggest options that would be
  unreasonable for the traveler's stated budget style.
- score reflects your confidence this recommendation fits the
  traveler well, from 0.0 (weak fit) to 1.0 (excellent fit).
- Suggest between 3 and 8 recommendations total."""


class RecommendationAgentPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="recommendation_agent", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(self, *, destination_names: list[str], itinerary_summary: str,
                            weather_summary: str, budget_summary: str) -> str:
        destinations = ", ".join(destination_names) or "unspecified"
        return (
            f"Trip destinations: {destinations}\n\n"
            f"Itinerary:\n{itinerary_summary}\n\n"
            f"Weather outlook:\n{weather_summary}\n\n"
            f"Budget context:\n{budget_summary}\n\n"
            f"Suggest additional recommendations that complement this trip."
        )
```

### 10.4 `ai/agents/recommendation_agent.py`

```python
"""
The join-point node. Depends on BOTH itinerary_plan (via
travel_planner, already in state) and weather_forecast (Chapter 14)
having completed. Also incorporates budget_estimate (Chapter 13) —
see Chapter 15 Architecture Decision for why this goes beyond
Architecture Handbook §9.3's stated two-input scope.
"""
from ai.agents.schemas import RecommendationBatchSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import TripPlanningState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.recommendation_agent_v1 import RecommendationAgentPromptV1

_prompt = RecommendationAgentPromptV1()


def _summarize_itinerary(itinerary_plan) -> str:
    lines = []
    for day in itinerary_plan.days:
        titles = ", ".join(item.title for item in day.items)
        lines.append(f"Day {day.day_number}: {titles}")
    return "\n".join(lines)


def _summarize_weather(weather_forecast: dict | None) -> str:
    if not weather_forecast:
        return "No weather data available."
    lines = [
        f"{d['date']}: {d['condition']}, {d['low_f']}-{d['high_f']}F, "
        f"{d['precipitation_chance']}% chance of rain"
        for d in weather_forecast["days"]
    ]
    return "\n".join(lines)


def _summarize_budget(budget_estimate: dict | None, budget_style: str) -> str:
    if not budget_estimate:
        return f"Traveler budget style: {budget_style}. No detailed estimate available."
    return (
        f"Traveler budget style: {budget_style}. "
        f"Estimated total trip cost so far: ${budget_estimate['total_estimate']}."
    )


def recommendation_agent_node(state: TripPlanningState, *, client: GroqClient | None = None) -> dict:
    client = client or GroqClient()

    user_prompt = _prompt.render_user_prompt(
        destination_names=state["destination_names"],
        itinerary_summary=_summarize_itinerary(state["itinerary_plan"]),
        weather_summary=_summarize_weather(state.get("weather_forecast")),
        budget_summary=_summarize_budget(state.get("budget_estimate"), state["budget_style"]),
    )

    batch: RecommendationBatchSchema = parse_structured_output(
        client=client,
        system_prompt=_prompt.system_prompt,
        user_prompt=user_prompt,
        schema=RecommendationBatchSchema,
        temperature=0.5,
    )

    return {"recommendations": [item.model_dump() for item in batch.items]}
```

**Why `_summarize_weather`/`_summarize_budget` both handle a `None`/missing input gracefully instead of assuming they're always present**: even though this chapter wires `recommendation_agent` to depend on both branches structurally, defensive handling here costs little and protects against a scenario Chapter 14 already established as valid — `weather_forecast` persistence is allowed to skip individual days, and a pathological case (all days skipped, or the weather branch producing an empty-but-technically-valid result) shouldn't crash this node outright; it should degrade gracefully to a less-informed but still-functioning recommendation.

**Why `state["destination_names"]` (from the *original* initial state, Chapter 12) is used here rather than trying to extract destinations from `itinerary_plan`**: the itinerary schema (Chapter 12) doesn't carry destination names on each item — only on the day/trip level, sourced from `Trip.destinations`. Reusing the same field the Travel Planner itself was given keeps this consistent and avoids re-deriving something already available in state.

### 10.5 `ai/graphs/planning_graph.py` (modified — the join)

```python
"""
The trip planning graph. FOUR nodes now, with the graph's first
join point: budget_agent AND weather_agent both feed into
recommendation_agent.
"""
from langgraph.graph import END, START, StateGraph

from ai.agents.budget_agent import budget_agent_node
from ai.agents.recommendation_agent import recommendation_agent_node
from ai.agents.travel_planner import travel_planner_node
from ai.agents.weather_agent import weather_agent_node
from ai.graphs.state import TripPlanningState


def build_planning_graph():
    graph = StateGraph(TripPlanningState)
    graph.add_node("travel_planner", travel_planner_node)
    graph.add_node("budget_agent", budget_agent_node)
    graph.add_node("weather_agent", weather_agent_node)
    graph.add_node("recommendation_agent", recommendation_agent_node)

    graph.add_edge(START, "travel_planner")
    graph.add_edge("travel_planner", "budget_agent")
    graph.add_edge("travel_planner", "weather_agent")

    # THE JOIN: recommendation_agent only runs once BOTH predecessors
    # below have completed.
    graph.add_edge("budget_agent", "recommendation_agent")
    graph.add_edge("weather_agent", "recommendation_agent")

    graph.add_edge("recommendation_agent", END)

    return graph.compile()


def run_planning_graph(initial_state: TripPlanningState) -> TripPlanningState:
    compiled_graph = build_planning_graph()
    return compiled_graph.invoke(initial_state)
```

**Why `budget_agent`'s and `weather_agent`'s previous direct edges to `END` (Chapter 14) are removed, not kept alongside the new edges to `recommendation_agent`**: a node can have multiple outgoing edges (that's how the *fork* in Chapter 14 worked), but here each of `budget_agent`/`weather_agent` has exactly **one** outgoing edge, to `recommendation_agent` — keeping the old `→ END` edges too would let the graph terminate along those paths *before* `recommendation_agent` ever runs, defeating the entire join. This is a genuine structural edit, not just an addition, worth calling out since every prior chapter's graph change was purely additive.

### 10.6 `apps/ai_agents/services.py` (addition)

```python
from apps.recommendations import services as recommendation_services


def _persist_recommendations(*, trip, recommendations: list[dict]) -> None:
    recommendation_services.clear_pending_ai_recommendations(trip=trip)

    destinations_by_name = {d.name.lower(): d for d in trip.destinations.all()}
    for item in recommendations:
        destination = destinations_by_name.get(item["destination_name"].lower())
        if destination is None:
            continue  # AI named a destination not linked to this trip — skip defensively
        recommendation_services.create_recommendation(
            trip=trip, destination=destination, category=item["category"],
            title=item["title"], description=item["description"], score=item["score"],
        )
```

Called from `run_travel_planner`, inside the same `transaction.atomic()` block:

```python
with transaction.atomic():
    _persist_itinerary_plan(trip=trip, plan=final_state["itinerary_plan"])
    if final_state.get("budget_estimate"):
        _persist_budget_estimate(trip=trip, estimate=final_state["budget_estimate"])
    if final_state.get("weather_forecast"):
        _persist_weather_forecast(trip=trip, forecast=final_state["weather_forecast"])
    if final_state.get("recommendations"):
        _persist_recommendations(trip=trip, recommendations=final_state["recommendations"])
```

**Why destination matching is case-insensitive (`.lower()` on both sides)**: the LLM might return `"tokyo"` where the destination catalog has `"Tokyo"` — matching exactly like Chapter 6's search (`icontains`, case-insensitive) prevents a trivial casing mismatch from silently discarding an otherwise-good recommendation.

**Why an unmatched destination is skipped, not defaulted to the trip's first destination**: defaulting would silently attach a recommendation to the *wrong* place, which is worse than not showing it at all — Chapter 10 already made `destination` a required field specifically because "a recommendation with no destination attached is not meaningful"; a recommendation attached to the *wrong* destination is arguably even less meaningful, so skipping (matching Chapter 14's weather-day skip philosophy) is the correct, consistent choice here too.

---

## 11. Code Walkthrough

- **The three regeneration strategies (Section 2.3) are now all real, tested code, side by side across three chapters** — itinerary's `day.items.all().delete()` (full replace, Chapter 12), budget's `filter(is_ai_estimated=True).delete()` (partial replace, Chapter 13), and this chapter's `filter(is_ai_generated=True, status=PENDING).delete()` (narrowest replace yet). Reading these three lines together is the single clearest illustration in the whole project of "the right amount of caution scales with what's actually at stake in the data."
- **`recommendation_agent_node` is the first node whose prompt-building helper functions (`_summarize_itinerary`, `_summarize_weather`, `_summarize_budget`) each read from a *different* upstream schema type**: this is worth noticing as the payoff of every prior agent producing clean, well-typed output — synthesizing three sources is straightforward specifically because each source was already validated and structured, not raw text the Recommendation Agent would otherwise have to parse itself.
- **The join point (Section 10.5) required editing two existing edges, not just adding new ones** — flagged explicitly because it's the first time in the AI layer's development that extending the graph wasn't purely additive, a useful contrast to keep in mind for Chapter 16 and Chapter 17's further graph changes.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `recommendation_agent_node` never runs / graph seems to hang or skip it | `budget_agent`/`weather_agent` still have leftover direct edges to `END` from Chapter 14's version, alongside the new edges | Confirm the old `graph.add_edge("budget_agent", END)` / `graph.add_edge("weather_agent", END)` lines were **removed**, not left in addition to the new ones |
| A recommendation the user already accepted disappears after a planner re-run | `clear_pending_ai_recommendations`'s status filter was loosened or removed | Restore the exact `is_ai_generated=True, status=PENDING` double filter — this would be a real, damaging bug for actual users |
| Recommendations silently missing for a destination you know the AI mentioned | Case-sensitivity or exact-name mismatch between the AI's `destination_name` and the catalog | Confirm the `.lower()` matching is in place; if the AI is inventing destination names not in the trip at all, that's a prompt-quality issue, not a persistence bug |
| `RecommendationBatchSchema` validation fails with "at most 15 items" | Model produced an implausibly large batch | Expected — Chapter 11's retry-with-correction flow handles this the same as any other schema violation |

---

## 13. Debugging

```bash
# 1. Confirm the join structure directly
docker compose exec web python manage.py shell -c "
from ai.graphs.planning_graph import build_planning_graph
graph = build_planning_graph()
edges = {(e.source, e.target) for e in graph.get_graph().edges}
print(('budget_agent', 'recommendation_agent') in edges)
print(('weather_agent', 'recommendation_agent') in edges)
print(('budget_agent', 'END') in edges)   # should be False now
"

# 2. Confirm accepted recommendations survive a manual re-persist call
docker compose exec web python manage.py shell -c "
from apps.trips.models import Trip
from apps.recommendations import services as rec_services
from apps.ai_agents.services import _persist_recommendations
trip = Trip.objects.first()
rec = trip.recommendations.first()
if rec:
    rec_services.accept_recommendation(recommendation=rec)
    _persist_recommendations(trip=trip, recommendations=[])
    rec.refresh_from_db()
    print('still exists after empty regen:', trip.recommendations.filter(pk=rec.pk).exists())
"
```

**Rollback strategy:** unchanged from Chapters 13-14 — the whole persistence step, including recommendations, is inside one `transaction.atomic()` block, so any failure leaves the trip's data exactly as it was before the run.

---

## 14. Testing

### 14.1 `ai/tests/test_recommendation_agent.py`

```python
from unittest.mock import MagicMock

from ai.agents.recommendation_agent import recommendation_agent_node
from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema


def test_recommendation_agent_node_returns_list_of_dicts():
    fake_client = MagicMock()
    fake_client.call.return_value = (
        '{"items": [{"destination_name": "Tokyo", "category": "restaurant", '
        '"title": "Try local ramen", "description": "", "score": 0.8}]}'
    )

    state = {
        "itinerary_plan": ItineraryPlanSchema(days=[
            ItineraryDaySchema(day_number=1, date="2026-06-01", items=[ItineraryItemSchema(title="Arrive")])
        ]),
        "weather_forecast": None,
        "budget_estimate": None,
        "budget_style": "moderate",
        "destination_names": ["Tokyo"],
    }

    result = recommendation_agent_node(state, client=fake_client)

    assert "recommendations" in result
    assert result["recommendations"][0]["title"] == "Try local ramen"


def test_recommendation_agent_node_handles_missing_weather_and_budget():
    fake_client = MagicMock()
    fake_client.call.return_value = '{"items": [{"destination_name": "Tokyo", "category": "activity", "title": "Walk", "score": 0.5}]}'

    state = {
        "itinerary_plan": ItineraryPlanSchema(days=[
            ItineraryDaySchema(day_number=1, date="2026-06-01", items=[ItineraryItemSchema(title="Arrive")])
        ]),
        "budget_style": "shoestring",
        "destination_names": ["Tokyo"],
        # weather_forecast and budget_estimate deliberately absent
    }

    result = recommendation_agent_node(state, client=fake_client)
    assert len(result["recommendations"]) == 1
```

### 14.2 `ai/tests/test_planning_graph.py` (additions)

```python
def test_recommendation_agent_is_a_join_point():
    from ai.graphs.planning_graph import build_planning_graph
    graph = build_planning_graph()
    edges = {(e.source, e.target) for e in graph.get_graph().edges}

    assert ("budget_agent", "recommendation_agent") in edges
    assert ("weather_agent", "recommendation_agent") in edges
    # the old direct-to-END edges from Chapter 14 must be gone
    assert ("budget_agent", "__end__") not in edges
    assert ("weather_agent", "__end__") not in edges
    assert ("recommendation_agent", "__end__") in edges
```

### 14.3 `apps/ai_agents/tests/test_services.py` (additions)

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.destinations.models import Destination
from apps.recommendations import services as rec_services
from apps.recommendations.models import Recommendation, RecommendationCategory
from apps.trips.models import Trip
from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema

User = get_user_model()


class RecommendationPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="rec@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1),
        )
        self.destination = Destination.objects.create(name="Tokyo", country="Japan")
        self.trip.destinations.add(self.destination)

    def _fake_state(self, recommendations):
        return {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[ItineraryItemSchema(title="Arrive")])
            ]),
            "recommendations": recommendations,
        }

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_recommendations_persisted_and_matched_by_destination_name(self, mock_graph):
        mock_graph.return_value = self._fake_state([
            {"destination_name": "Tokyo", "category": "activity", "title": "Visit shrine", "description": "", "score": 0.9},
        ])
        services.run_travel_planner(trip=self.trip)
        self.assertEqual(Recommendation.objects.filter(trip=self.trip).count(), 1)
        self.assertEqual(Recommendation.objects.get(trip=self.trip).destination, self.destination)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_unmatched_destination_name_skipped(self, mock_graph):
        mock_graph.return_value = self._fake_state([
            {"destination_name": "Nowhere City", "category": "activity", "title": "???", "description": "", "score": 0.5},
        ])
        services.run_travel_planner(trip=self.trip)
        self.assertEqual(Recommendation.objects.filter(trip=self.trip).count(), 0)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_accepted_recommendation_survives_rerun(self, mock_graph):
        mock_graph.return_value = self._fake_state([
            {"destination_name": "Tokyo", "category": "activity", "title": "Visit shrine", "description": "", "score": 0.9},
        ])
        services.run_travel_planner(trip=self.trip)
        rec = Recommendation.objects.get(trip=self.trip)
        rec_services.accept_recommendation(recommendation=rec)

        mock_graph.return_value = self._fake_state([
            {"destination_name": "Tokyo", "category": "restaurant", "title": "New suggestion", "description": "", "score": 0.7},
        ])
        services.run_travel_planner(trip=self.trip)

        self.assertTrue(Recommendation.objects.filter(pk=rec.pk, status="accepted").exists())
        self.assertEqual(Recommendation.objects.filter(trip=self.trip).count(), 2)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_pending_recommendation_is_replaced_on_rerun(self, mock_graph):
        mock_graph.return_value = self._fake_state([
            {"destination_name": "Tokyo", "category": "activity", "title": "Old suggestion", "description": "", "score": 0.5},
        ])
        services.run_travel_planner(trip=self.trip)

        mock_graph.return_value = self._fake_state([
            {"destination_name": "Tokyo", "category": "activity", "title": "New suggestion", "description": "", "score": 0.5},
        ])
        services.run_travel_planner(trip=self.trip)

        titles = set(Recommendation.objects.filter(trip=self.trip).values_list("title", flat=True))
        self.assertEqual(titles, {"New suggestion"})
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.recommendations -v 2
```

---

## 15. Git Commit

```bash
git add apps/recommendations/services.py ai/agents/ ai/prompts/recommendation_agent_v1.py ai/graphs/planning_graph.py apps/ai_agents/services.py ai/tests/ apps/ai_agents/tests/test_services.py
git commit -m "feat(ai_agents): Recommendation Agent — graph's first join point

- planning_graph.py: budget_agent AND weather_agent's direct-to-END
  edges REMOVED (not just added-to) and replaced with edges into
  recommendation_agent — the graph's first genuinely structural edit,
  not a purely additive one; LangGraph waits for both predecessors
  before running the join node
- recommendation_agent synthesizes itinerary + weather + budget;
  budget input deliberately extends beyond Architecture Handbook
  §9.3's stated two-input scope, justified explicitly (avoid
  recommending options mismatched to the traveler's budget style)
- Three regeneration strategies now exist side by side across
  Chapters 12/13/15: itinerary full-replace, budget AI-only replace,
  recommendations pending-AI-only replace — each justified by what's
  genuinely at stake in that model's data (plan vs actuals vs user
  decision)
- clear_pending_ai_recommendations() NEVER touches accepted/rejected
  recommendations, tested explicitly with a rerun scenario
- Destination name resolution is case-insensitive; unmatched names
  are skipped, never defaulted to the wrong destination (consistent
  with Chapter 10's required-FK decision and Chapter 14's skip
  philosophy)
- apps/recommendations/services.py gains create_recommendation() and
  clear_pending_ai_recommendations() — ai_agents still never writes
  to another app's model directly

Chapter 15 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `recommendation_agent` has exactly two incoming edges (`budget_agent`, `weather_agent`); their old direct-to-`END` edges are gone
- [ ] Graph structure test confirms the join, including the *absence* of the old edges
- [ ] `RecommendationBatchSchema` bounds batch size (1-15), matching the "catch degenerate output" pattern from every prior schema
- [ ] `clear_pending_ai_recommendations` filters on **both** `is_ai_generated=True` and `status=PENDING` — verified by a test that an accepted recommendation survives a re-run
- [ ] Destination name matching is case-insensitive; unmatched names are skipped, not defaulted
- [ ] `_persist_recommendations` goes through `apps.recommendations.services`, never a raw `Recommendation.objects.create()` in `ai_agents`
- [ ] Full persistence (itinerary, budget, weather, recommendations) still wrapped in one `transaction.atomic()` block
- [ ] All tests passing across `ai/tests`, `apps.ai_agents`, `apps.recommendations`
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 16 — Packing Agent** is the final individual agent chapter, and the node with the richest input of all — it consumes weather, itinerary, and trip length together to build a packing checklist. This is also where the graph's shape settles into its final form before Chapter 17 does nothing but wiring: `recommendation_agent → packing_agent → END`, making Packing the true last stop, exactly matching Architecture Handbook §9.2's diagram in full for the first time. Say **"Continue to Chapter 16"** when ready.
