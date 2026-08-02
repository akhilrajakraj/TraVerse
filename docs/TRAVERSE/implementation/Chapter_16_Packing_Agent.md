# Chapter 16 — Packing Agent

**Volume 4: AI Layer | Chapter 16 of 29**

> The final individual agent chapter. `packing_agent` sits at the very end of the chain — `recommendation_agent → packing_agent → END` — and has the richest input of any agent so far, synthesizing weather, itinerary, and trip length into a checklist. After this chapter, the graph finally matches Architecture Handbook §9.2's full diagram exactly. Chapter 17 does no new agent work at all — it only wires, renames, and hardens what these five chapters already built.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Design an agent that reads from state fields populated by three different upstream nodes, and reason about what happens when some of those inputs are optional/missing.
- Recognize and correct a speculative design decision from an earlier chapter once its real requirements become clear, and document that correction honestly rather than silently.
- Model a new trip-level, checkable (not just AI-decided) list — `PackingItem` — including a genuine user-facing feature (checking items off) alongside AI generation.
- Recognize the graph's final shape as now matching Architecture Handbook §9.2 in full, and understand exactly what work is deliberately left for Chapter 17.

---

## 2. Theory

### 2.1 Why Packing Needs the *Most* Inputs of Any Agent (ELI10)

Think about what actually determines a packing list: how long the trip is (itinerary length), what the weather will be like (pack a coat or not), and what activities are planned (hiking boots for a hike, formal wear for a nice dinner). No other agent in this project needs to look at *three* upstream signals simultaneously the way Packing does — Budget only needed the itinerary (Chapter 13), Weather only needed destinations/dates (Chapter 14), Recommendation needed itinerary + weather + budget (Chapter 15) but for a different reason (matching recommendations to context, not enumerating physical items). Packing is the natural "last stop" precisely because it's the agent most dependent on *everything else already being decided*.

### 2.2 Why This Chapter Corrects Chapter 12's `packing_list: list[str]` Guess

Chapter 12 sized `TripPlanningState` ahead of need, reserving four fields for agents that didn't exist yet. Three of those guesses (`budget_estimate: dict`, `weather_forecast: dict`, `recommendations: list[dict]`) turned out to match what Chapters 13-15 actually needed. The fourth, `packing_list: list[str]`, does not — a packing list is far more useful as **structured items** (each with a category, a quantity, and whether it's essential) than as plain strings a UI would have to parse or guess at. This is worth calling out honestly, not quietly fixed: Chapter 12 made a reasonable guess with the information available at the time, and this chapter corrects it now that the real shape is known — exactly the kind of revision real engineering involves, and a healthier lesson than pretending every early decision was perfect in hindsight.

### 2.3 Why Packing Items Get a Genuine User Feature (`is_packed`) That No Other AI-Touched Model Has

Every other AI-populated model so far is either read-only from the user's side (`Recommendation`, decided via accept/reject) or freely editable (`ItineraryItem`, `BudgetLineItem`). A packing list is different in a small but real way: a user doesn't *decide whether an item belongs on the list* the way they decide on a recommendation — they check items off as they physically pack them. `is_packed` models that specific interaction, not a duplicate of any pattern already built.

---

## 3. Architecture Decision

**Decision:** `TripPlanningState.packing_list`'s type is corrected from `list[str] | None` (Chapter 12's speculative guess) to `list[dict] | None`, matching the pattern already used for `budget_estimate`/`recommendations`.

**Decision:** `PackingItem` is added to `apps/trips/models.py`, not a new dedicated app.

**Alternative considered:** Create a new `packing` Django app. **Rejected because:** Architecture Handbook §4.2's app catalog never lists a `packing` app — packing is explicitly called out in §7.2 as "part of itinerary or its own model," and a trip-level, non-hierarchical list of items fits naturally as a direct child of `Trip` (the same shape as Chapter 10's `Recommendation`, which also FKs `Trip` directly with no intermediate model) — adding a whole new app for one small model would be structural overkill, the same YAGNI judgment already applied to `django-filter` (Chapter 6) and the built-in weather lookup (Chapter 14).

**Decision:** Regenerating the packing list clears **all** AI-generated items (`is_ai_generated=True`), regardless of their `is_packed` state, then recreates fresh ones.

**Trade-off documented:** unlike a `Recommendation`'s accept/reject decision (Chapter 15), a checked-off packing item has no natural "same item" identity to preserve across a regeneration — the itinerary or weather may have genuinely changed, changing what should be on the list at all. This is an accepted, documented UX trade-off (a user might lose their checkmarks on a re-run), not an oversight; building fuzzy item-matching to preserve checkmarks is explicitly out of scope here as a YAGNI call, revisitable later if real user feedback demands it.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Correct `TripPlanningState.packing_list`'s type | Needed before the node's return value can be typed correctly |
| Add `PackingItem` model + migration to `apps/trips` | Needed before anything can persist packing data |
| Add `apps/trips/services.py` packing functions | Needed before `ai_agents` can persist through it |
| Write `ai/agents/schemas.py` additions | Needed before the prompt/node |
| Write `ai/prompts/packing_agent_v1.py` and `ai/agents/packing_agent.py` | Needed before the graph |
| Add the final node + edge, remove `recommendation_agent`'s old `→ END` edge | Needed before `ai_agents` sees `packing_list` in final state |
| Extend `apps/ai_agents/services.py` with `_persist_packing_list` | Last |
| Build the read/toggle API (`GET`/`PATCH /trips/{id}/packing/`) | Genuinely last — the user-facing feature on top of everything else |

---

## 5. File Structure

```
ai/
├── graphs/
│   ├── state.py                    # MODIFIED — packing_list type corrected
│   └── planning_graph.py            # MODIFIED — final node + edge
├── agents/
│   ├── schemas.py                   # MODIFIED — PackingItemSchema, PackingListSchema
│   └── packing_agent.py              # NEW
└── prompts/
    └── packing_agent_v1.py            # NEW

apps/trips/
├── models.py                     # MODIFIED — adds PackingItem
├── services.py                    # MODIFIED — add_packing_item, clear_ai_packing_items
├── serializers.py                  # MODIFIED — PackingItemSerializer
├── views.py                        # MODIFIED — TripPackingListView, PackingItemToggleView
├── urls.py                         # MODIFIED
└── migrations/
    └── 0002_packingitem.py            # NEW

apps/ai_agents/
└── services.py                    # MODIFIED — _persist_packing_list

ai/tests/
├── test_packing_agent.py            # NEW
└── test_planning_graph.py            # MODIFIED — asserts final graph shape
apps/trips/tests/
├── test_models.py                  # MODIFIED
├── test_services.py                 # MODIFIED
└── test_views.py                    # MODIFIED
```

---

## 6. Folder Location

Modified/new files under `ai/`, `apps/trips/`, `apps/ai_agents/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations trips
docker compose exec web python manage.py migrate

docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.trips -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web celery
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations trips
Migrations for 'trips':
  apps/trips/migrations/0002_packingitem.py
    - Create model PackingItem

$ curl http://localhost:8000/api/v1/trips/<trip_id>/packing/ -H "Authorization: Bearer <access>"
{
  "results": [
    {"id": 1, "category": "clothing", "item_name": "Rain jacket", "quantity": 1, "is_essential": true, "is_packed": false}
  ]
}
```

---

## 10. Code

### 10.1 `ai/graphs/state.py` (corrected)

```python
class TripPlanningState(TypedDict, total=False):
    # ... unchanged fields from Chapter 12 ...

    # CORRECTED in Chapter 16 — was list[str] in Chapter 12's
    # speculative sizing; structured items are more useful than
    # plain strings. See Chapter 16 Theory §2.2 for why this is the
    # one reserved field that needed revising, not just filling in.
    packing_list: list[dict] | None
```

### 10.2 `apps/trips/models.py` (addition)

```python
class PackingCategory(models.TextChoices):
    CLOTHING = "clothing", "Clothing"
    TOILETRIES = "toiletries", "Toiletries"
    ELECTRONICS = "electronics", "Electronics"
    DOCUMENTS = "documents", "Documents"
    GEAR = "gear", "Gear"
    OTHER = "other", "Other"


class PackingItem(TimeStampedModel):
    """
    Trip-level packing checklist item. Direct FK to Trip, no
    intermediate model — same shape as Chapter 10's Recommendation.
    """
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="packing_items")
    category = models.CharField(max_length=20, choices=PackingCategory.choices)
    item_name = models.CharField(max_length=150)
    quantity = models.PositiveSmallIntegerField(default=1)
    is_essential = models.BooleanField(default=True)
    is_packed = models.BooleanField(
        default=False,
        help_text="User-toggled — unlike Recommendation's accept/reject, this "
                   "tracks a physical action (did I pack it), not a decision "
                   "about whether the item belongs on the list.",
    )
    is_ai_generated = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "item_name"]
        indexes = [models.Index(fields=["trip", "category"])]
        verbose_name = "Packing Item"
        verbose_name_plural = "Packing Items"

    def __str__(self) -> str:
        return f"{self.item_name} ({self.trip.title})"
```

**Why `is_ai_generated` defaults to `True`, matching `Recommendation`'s default rather than `ItineraryItem`/`BudgetLineItem`'s `False`**: same reasoning as Chapter 10 — a packing list is something a user is unlikely to build entirely from scratch themselves; the AI-generated case is the common one here too.

### 10.3 `apps/trips/services.py` (addition)

```python
def add_packing_item(*, trip: Trip, category: str, item_name: str, quantity: int = 1,
                      is_essential: bool = True, is_ai_generated: bool = True) -> PackingItem:
    return PackingItem.objects.create(
        trip=trip, category=category, item_name=item_name, quantity=quantity,
        is_essential=is_essential, is_ai_generated=is_ai_generated,
    )


def clear_ai_packing_items(*, trip: Trip) -> None:
    """
    Clears ALL AI-generated packing items regardless of is_packed
    state on regeneration — see Chapter 16 Architecture Decision for
    the documented UX trade-off (checkmarks may be lost on re-run).
    User-added items (is_ai_generated=False) are never touched.
    """
    trip.packing_items.filter(is_ai_generated=True).delete()


def toggle_packing_item(*, item: PackingItem) -> PackingItem:
    item.is_packed = not item.is_packed
    item.save(update_fields=["is_packed", "updated_at"])
    return item
```

### 10.4 `ai/agents/schemas.py` (addition)

```python
"""
(appended to schemas.py from Chapters 12-15)
"""


class PackingItemSchema(BaseModel):
    category: str = Field(..., pattern="^(clothing|toiletries|electronics|documents|gear|other)$")
    item_name: str = Field(..., max_length=150)
    quantity: int = Field(default=1, ge=1, le=20)
    is_essential: bool = True


class PackingListSchema(BaseModel):
    items: list[PackingItemSchema] = Field(..., min_length=1, max_length=40)
```

**Why `quantity` is bounded `ge=1, le=20`**: zero of an item makes no sense on a packing list (it wouldn't be listed at all), and a suggestion of, say, 50 pairs of socks is an obvious degenerate output — the same bound-catching instinct as every prior schema, sized to what's plausible for this specific domain.

### 10.5 `ai/prompts/packing_agent_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a travel packing assistant.
Given a trip's itinerary, weather outlook, and duration, produce a
practical packing checklist.

Rules:
- Respond with ONLY valid JSON matching the provided schema.
- Categories must be exactly one of: clothing, toiletries,
  electronics, documents, gear, other.
- Scale clothing quantities sensibly to trip duration (e.g. don't
  suggest 14 shirts for a 3-day trip).
- Mark items essential=true only for genuinely critical items
  (passport, medication, weather-critical gear) — most items should
  be essential=false.
- Reflect the weather outlook: suggest rain gear for wet conditions,
  warm layers for cold conditions, sun protection for hot/sunny
  conditions.
- Reflect specific planned activities where relevant (e.g. hiking
  boots if a hike is on the itinerary)."""


class PackingAgentPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="packing_agent", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(self, *, trip_duration_days: int, itinerary_summary: str,
                            weather_summary: str, traveler_count: int) -> str:
        return (
            f"Trip duration: {trip_duration_days} day(s)\n"
            f"Number of travelers: {traveler_count}\n\n"
            f"Itinerary:\n{itinerary_summary}\n\n"
            f"Weather outlook:\n{weather_summary}\n\n"
            f"Produce a complete packing checklist for this trip."
        )
```

### 10.6 `ai/agents/packing_agent.py`

```python
"""
The final node in the planning graph. Reads itinerary_plan,
weather_forecast, and trip duration — the richest input of any
agent, per Chapter 16 Theory §2.1.
"""
from datetime import date

from ai.agents.schemas import PackingListSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import TripPlanningState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.packing_agent_v1 import PackingAgentPromptV1

_prompt = PackingAgentPromptV1()


def _summarize_itinerary(itinerary_plan) -> str:
    lines = []
    for day in itinerary_plan.days:
        titles = ", ".join(item.title for item in day.items)
        lines.append(f"Day {day.day_number}: {titles}")
    return "\n".join(lines)


def _summarize_weather(weather_forecast: dict | None) -> str:
    if not weather_forecast:
        return "No weather data available — pack general-purpose items."
    conditions = {d["condition"] for d in weather_forecast["days"]}
    return f"Conditions expected: {', '.join(sorted(conditions))}."


def _trip_duration_days(state: TripPlanningState) -> int:
    start = date.fromisoformat(state["start_date"])
    end = date.fromisoformat(state["end_date"])
    return (end - start).days + 1


def packing_agent_node(state: TripPlanningState, *, client: GroqClient | None = None) -> dict:
    client = client or GroqClient()

    user_prompt = _prompt.render_user_prompt(
        trip_duration_days=_trip_duration_days(state),
        itinerary_summary=_summarize_itinerary(state["itinerary_plan"]),
        weather_summary=_summarize_weather(state.get("weather_forecast")),
        traveler_count=state.get("traveler_count", 1),
    )

    packing_list: PackingListSchema = parse_structured_output(
        client=client,
        system_prompt=_prompt.system_prompt,
        user_prompt=user_prompt,
        schema=PackingListSchema,
        temperature=0.4,
    )

    return {"packing_list": [item.model_dump() for item in packing_list.items]}
```

**Why `state.get("traveler_count", 1)` uses `.get()` with a default, when every other field access on `itinerary_plan` uses direct indexing (`state["itinerary_plan"]`)**: `traveler_count` was never actually added to `TripPlanningState` or `_build_initial_state` in any prior chapter — this is a deliberate, small gap left for `ai_agents` to fill in Section 10.9 (adding it to the initial state), with the node defensively defaulting in the meantime so it doesn't hard-crash if that wiring is ever momentarily out of sync — worth noting as a real, small loose end being handled gracefully rather than silently ignored.

### 10.7 `ai/graphs/planning_graph.py` (modified — final shape)

```python
"""
The trip planning graph — FINAL SHAPE, matching Architecture
Handbook §9.2 in full:
travel_planner -> {budget_agent, weather_agent} -> recommendation_agent
-> packing_agent -> END
"""
from langgraph.graph import END, START, StateGraph

from ai.agents.budget_agent import budget_agent_node
from ai.agents.packing_agent import packing_agent_node
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
    graph.add_node("packing_agent", packing_agent_node)

    graph.add_edge(START, "travel_planner")
    graph.add_edge("travel_planner", "budget_agent")
    graph.add_edge("travel_planner", "weather_agent")
    graph.add_edge("budget_agent", "recommendation_agent")
    graph.add_edge("weather_agent", "recommendation_agent")
    graph.add_edge("recommendation_agent", "packing_agent")
    graph.add_edge("packing_agent", END)

    return graph.compile()


def run_planning_graph(initial_state: TripPlanningState) -> TripPlanningState:
    compiled_graph = build_planning_graph()
    return compiled_graph.invoke(initial_state)
```

**Why `recommendation_agent`'s old `→ END` edge (Chapter 15) is removed, replaced by `→ packing_agent`**: the same structural-edit pattern as Chapter 15's own edit to `budget_agent`/`weather_agent` — `packing_agent` becomes the sole new terminus, and the graph now has exactly one path to `END`, from `packing_agent` alone, matching a genuinely linear-after-the-join final stretch.

### 10.8 `apps/ai_agents/services.py` (additions)

```python
from apps.trips import services as trip_packing_services  # add_packing_item, clear_ai_packing_items


def _persist_packing_list(*, trip, items: list[dict]) -> None:
    trip_packing_services.clear_ai_packing_items(trip=trip)
    for item in items:
        trip_packing_services.add_packing_item(
            trip=trip, category=item["category"], item_name=item["item_name"],
            quantity=item["quantity"], is_essential=item["is_essential"],
        )
```

`_build_initial_state` gains `traveler_count`, closing the small gap flagged in Section 10.6:

```python
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
        "traveler_count": trip.traveler_count,   # NEW — closes packing_agent's gap
    }
```

And the final persistence block, now covering all five agents' output:

```python
with transaction.atomic():
    _persist_itinerary_plan(trip=trip, plan=final_state["itinerary_plan"])
    if final_state.get("budget_estimate"):
        _persist_budget_estimate(trip=trip, estimate=final_state["budget_estimate"])
    if final_state.get("weather_forecast"):
        _persist_weather_forecast(trip=trip, forecast=final_state["weather_forecast"])
    if final_state.get("recommendations"):
        _persist_recommendations(trip=trip, recommendations=final_state["recommendations"])
    if final_state.get("packing_list"):
        _persist_packing_list(trip=trip, items=final_state["packing_list"])
```

### 10.9 `apps/trips/serializers.py` / `views.py` / `urls.py` (additions)

```python
# serializers.py
class PackingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackingItem
        fields = ["id", "category", "item_name", "quantity", "is_essential", "is_packed", "is_ai_generated"]
        read_only_fields = ["id", "category", "item_name", "quantity", "is_essential", "is_ai_generated"]
        # is_packed is the ONLY field a client may write via this serializer
```

```python
# views.py
class TripPackingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        items = trip.packing_items.all()
        return Response(PackingItemSerializer(items, many=True).data)


class PackingItemToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk, item_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        item = get_object_or_404(PackingItem, pk=item_pk, trip=trip)
        updated = trip_services.toggle_packing_item(item=item)
        return Response(PackingItemSerializer(updated).data)
```

```python
# urls.py (additions)
path("<uuid:trip_pk>/packing/", TripPackingListView.as_view(), name="packing-list"),
path("<uuid:trip_pk>/packing/<int:item_pk>/toggle/", PackingItemToggleView.as_view(), name="packing-toggle"),
```

**Why toggling is its own dedicated `POST .../toggle/` endpoint rather than a generic `PATCH` accepting `{"is_packed": true/false}`**: this is the same "explicit over generic" instinct behind Chapter 7's `/trips/{id}/status/` and Chapter 10's `/accept/`/`/reject/` endpoints — a toggle is a single, unambiguous action, and `read_only_fields` on `PackingItemSerializer` structurally prevents `is_packed` (or anything else) from being written through the general serializer at all, closing off any other path to modifying it.

---

## 11. Code Walkthrough

- **This is the first chapter to *revise* a Chapter 12 decision rather than only extend it** — `packing_list`'s type correction (Section 10.1) is a small but important precedent: forward-planning (Chapter 12's whole strategy) reduces churn on average, but it doesn't guarantee every guess is right, and this project handles being wrong by fixing it once, cleanly, with the reasoning on record — not by working around a bad guess forever.
- **The graph's final shape (Section 10.7) now has exactly one join (into `recommendation_agent`) and exactly one linear tail (`recommendation_agent → packing_agent → END`)** — worth visualizing mentally against Architecture Handbook §9.2's original diagram one more time: five nodes, one fork, one join, one tail, now fully real.
- **`PackingItem` is the second model (after `Recommendation`) to be a direct child of `Trip` with no intermediate model**, and the second to default `is_ai_generated=True` — recognizing this as a recurring shape (`Trip → many AI-populated items, no hierarchy needed`) versus the two-level shape used by `itinerary`/`budget` is a genuinely useful modeling instinct to carry forward into any future app.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `KeyError: 'traveler_count'` inside `packing_agent_node` | `_build_initial_state` wasn't updated to include it | Confirm Section 10.8's addition is applied; the node's `.get(..., 1)` default only protects against a *missing* key, not against a wrong value if the key exists but is stale |
| Packing list looks identical every time regardless of weather changes | `_summarize_weather` collapsing to a generic string because `weather_forecast` wasn't actually populated (e.g., weather branch failed) | Check the corresponding `AgentRun` / logs for weather agent issues; packing quality is only as good as its inputs |
| User's checked-off items reset after a re-run | Expected, documented behavior (Architecture Decision) — not a bug | If this becomes a real user complaint, revisit the fuzzy-matching option explicitly deferred here |
| `is_packed` can't be set via the general trip/packing update flow | Confusing this endpoint with a generic PATCH | Use the dedicated `/packing/{item_id}/toggle/` endpoint — this is by design, not a missing feature |

---

## 13. Debugging

```bash
# 1. Confirm the graph's final shape end-to-end
docker compose exec web python manage.py shell -c "
from ai.graphs.planning_graph import build_planning_graph
graph = build_planning_graph()
edges = sorted((e.source, e.target) for e in graph.get_graph().edges)
for e in edges: print(e)
"

# 2. Run the full five-agent graph manually against a real trip (uses the real Groq API — costs real tokens)
docker compose exec web python manage.py shell -c "
from apps.ai_agents import services
from apps.trips.models import Trip
trip = Trip.objects.first()
run = services.run_travel_planner(trip=trip)
print(run.status)
print('itinerary days:', trip.itinerary_days.count())
print('budget items:', trip.budget.line_items.count())
print('recommendations:', trip.recommendations.count())
print('packing items:', trip.packing_items.count())
"
```

**Rollback strategy:** unchanged — the whole five-part persistence sequence is inside one `transaction.atomic()` block.

---

## 14. Testing

### 14.1 `ai/tests/test_packing_agent.py`

```python
from unittest.mock import MagicMock

from ai.agents.packing_agent import packing_agent_node
from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema


def test_packing_agent_node_returns_list_of_dicts():
    fake_client = MagicMock()
    fake_client.call.return_value = (
        '{"items": [{"category": "clothing", "item_name": "Rain jacket", '
        '"quantity": 1, "is_essential": true}]}'
    )

    state = {
        "itinerary_plan": ItineraryPlanSchema(days=[
            ItineraryDaySchema(day_number=1, date="2026-06-01", items=[ItineraryItemSchema(title="Hike")])
        ]),
        "weather_forecast": None,
        "start_date": "2026-06-01", "end_date": "2026-06-03",
        "traveler_count": 2,
    }

    result = packing_agent_node(state, client=fake_client)

    assert result["packing_list"][0]["item_name"] == "Rain jacket"


def test_trip_duration_calculated_inclusively():
    from ai.agents.packing_agent import _trip_duration_days
    state = {"start_date": "2026-06-01", "end_date": "2026-06-03"}
    assert _trip_duration_days(state) == 3  # inclusive of both endpoints
```

### 14.2 `ai/tests/test_planning_graph.py` (final additions)

```python
def test_full_graph_matches_architecture_handbook_shape():
    from ai.graphs.planning_graph import build_planning_graph
    graph = build_planning_graph()
    node_names = set(graph.get_graph().nodes.keys())
    edges = {(e.source, e.target) for e in graph.get_graph().edges}

    expected_nodes = {"travel_planner", "budget_agent", "weather_agent", "recommendation_agent", "packing_agent"}
    assert expected_nodes.issubset(node_names)

    assert ("travel_planner", "budget_agent") in edges
    assert ("travel_planner", "weather_agent") in edges
    assert ("budget_agent", "recommendation_agent") in edges
    assert ("weather_agent", "recommendation_agent") in edges
    assert ("recommendation_agent", "packing_agent") in edges
    assert ("packing_agent", "__end__") in edges
    # exactly one path reaches END now
    assert ("recommendation_agent", "__end__") not in edges
```

### 14.3 `apps/trips/tests/test_services.py` (additions)

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.trips import services
from apps.trips.models import PackingItem, Trip

User = get_user_model()


class PackingItemServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="p@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))

    def test_add_packing_item(self):
        item = services.add_packing_item(trip=self.trip, category="clothing", item_name="Socks", quantity=5)
        self.assertEqual(item.quantity, 5)

    def test_clear_ai_packing_items_preserves_manual(self):
        services.add_packing_item(trip=self.trip, category="clothing", item_name="AI item", is_ai_generated=True)
        services.add_packing_item(trip=self.trip, category="documents", item_name="Passport", is_ai_generated=False)

        services.clear_ai_packing_items(trip=self.trip)

        remaining = list(PackingItem.objects.filter(trip=self.trip).values_list("item_name", flat=True))
        self.assertEqual(remaining, ["Passport"])

    def test_toggle_packing_item(self):
        item = services.add_packing_item(trip=self.trip, category="gear", item_name="Camera")
        self.assertFalse(item.is_packed)
        services.toggle_packing_item(item=item)
        item.refresh_from_db()
        self.assertTrue(item.is_packed)
```

### 14.4 `apps/ai_agents/tests/test_services.py` (final additions)

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.trips.models import PackingItem, Trip
from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema

User = get_user_model()


class PackingPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="pack@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3),
        )

    def _fake_state(self, packing_list):
        return {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[ItineraryItemSchema(title="Arrive")])
            ]),
            "packing_list": packing_list,
        }

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_packing_items_persisted(self, mock_graph):
        mock_graph.return_value = self._fake_state([
            {"category": "clothing", "item_name": "Jacket", "quantity": 1, "is_essential": True},
        ])
        services.run_travel_planner(trip=self.trip)
        self.assertEqual(PackingItem.objects.filter(trip=self.trip).count(), 1)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_initial_state_includes_traveler_count(self, mock_graph):
        mock_graph.return_value = self._fake_state([])
        services.run_travel_planner(trip=self.trip)
        passed_state = mock_graph.call_args[0][0]
        self.assertIn("traveler_count", passed_state)
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.trips -v 2
```

---

## 15. Git Commit

```bash
git add ai/graphs/ ai/agents/ ai/prompts/packing_agent_v1.py apps/trips/ apps/ai_agents/services.py ai/tests/
git commit -m "feat(ai_agents): Packing Agent — final graph node, graph reaches full shape

- TripPlanningState.packing_list CORRECTED from Chapter 12's
  speculative list[str] to list[dict] — documented honestly as the
  one reserved field whose real shape wasn't known in advance,
  unlike budget_estimate/weather_forecast/recommendations which
  matched their eventual chapters exactly
- PackingItem added to apps/trips (not a new app) — direct Trip FK,
  same shape as Chapter 10's Recommendation, no intermediate model
  needed for a flat trip-level list
- is_packed: the first field in the project modeling a physical
  user action (did I pack it) rather than a decision or edit —
  distinct in kind from Recommendation's accept/reject
- clear_ai_packing_items() clears ALL AI items regardless of
  is_packed state on regen — documented UX trade-off (checkmarks
  may be lost), fuzzy-matching explicitly deferred as YAGNI
- planning_graph.py reaches its FINAL shape: travel_planner ->
  {budget_agent, weather_agent} -> recommendation_agent ->
  packing_agent -> END, now matching Architecture Handbook §9.2 in
  full; recommendation_agent's old ->END edge removed
- _build_initial_state gains traveler_count, closing a small gap the
  packing agent's node flagged defensively
- Dedicated POST .../packing/{id}/toggle/ endpoint; is_packed is the
  ONLY field writable through PackingItemSerializer at all

Final individual-agent chapter. Chapter 17 does wiring/renaming/
hardening only — no new agent logic. Chapter 16 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `TripPlanningState.packing_list` corrected to `list[dict] | None`, with the correction documented as intentional, not silent
- [ ] `PackingItem` lives in `apps/trips`, not a new app — reasoning matches Architecture Handbook §7.2's own hint
- [ ] `is_packed` is the only field writable via `PackingItemSerializer`; toggling has its own dedicated endpoint
- [ ] `clear_ai_packing_items` preserves manually-added items, tested explicitly
- [ ] Graph's final shape verified: exactly one join, one linear tail, `packing_agent` the sole predecessor of `END`
- [ ] `_build_initial_state` includes `traveler_count`; verified by inspecting the state actually passed to the graph in a test
- [ ] `PackingItemSchema` bounds `quantity` (1-20) and constrains `category` to the valid set
- [ ] All tests passing across `ai/tests`, `apps.ai_agents`, `apps.trips`
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 17 — LangGraph Orchestration Assembly** does no new agent-building work — the graph already has its final shape. Instead, it: renames `AgentRun.agent_type` from the placeholder `TRAVEL_PLANNER` (used since Chapter 12 for the whole multi-agent run) to the already-reserved `FULL_GRAPH`, with a proper data migration for any existing rows; adds end-to-end integration tests that exercise the real five-node graph together (still with a mocked LLM, per Architecture Handbook §11's testing strategy); and reviews Celery task configuration now that a single `/plan/` trigger runs meaningfully more work than it did in Chapter 12. This is the "close out Volume 4" chapter. Say **"Continue to Chapter 17"** when ready.
