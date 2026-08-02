# Chapter 14 — Weather Agent

**Volume 4: AI Layer | Chapter 14 of 29**

> Two firsts in this chapter. First: genuine tool-calling — rather than only reasoning over text, the Weather Agent lets the LLM decide to call a Python function mid-conversation, per Architecture Handbook §9.6. Second: the graph's *shape* changes for the first time — Weather branches off the Travel Planner in parallel with the Budget Agent (Chapter 13), rather than extending a single chain. Both agents depend only on the itinerary, not on each other, matching Architecture Handbook §9.2's diagram exactly.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Extend the single-door `GroqClient` (Chapter 11) to support LLM tool-calling, while keeping the existing plain-text `call()` method's behavior and callers completely unchanged.
- Register a plain Python function as an LLM-callable tool, and understand the two-way message exchange (tool call request → tool result → final answer) tool-calling requires.
- Wire true parallel branches in LangGraph (two nodes with the same predecessor), and verify a state merge with no field-name collisions.
- Explain why "typical seasonal weather," not a live forecast, is the architecturally correct choice for a trip planned months in advance — a domain judgment call, not just a technical one.

---

## 2. Theory

### 2.1 What "The LLM Decides When To Call a Tool" Actually Means (ELI10)

In Chapters 12-13, the LLM only ever did one thing: read a prompt, write an answer. A tool-calling agent is different — instead of answering directly, the model can say "before I answer, I need to call `get_typical_weather` with these arguments." Our code then actually runs that Python function, hands the *real* result back to the model, and only then does the model produce its final answer, now grounded in real data it didn't have to guess. Architecture Handbook §9.6 states the safety principle exactly: "The LLM decides *when* to call them; our code guarantees *what* they return is validated and safe" — the model chooses *when*, but never executes anything itself; our code is always the one actually running the function.

### 2.2 Why "Typical Seasonal Weather," Not a Live Forecast (ELI10)

Real weather forecasts are only meaningfully accurate roughly one to two weeks out. A trip planned three months in advance simply cannot get a real forecast for its actual travel dates — asking a live weather API for "the weather in Tokyo on a date five months from now" would return either an error or a meaningless placeholder. What a traveler actually needs at planning time is "what's Tokyo *typically* like in October" — seasonal, climatological information, which is stable and genuinely knowable months ahead. This chapter's tool is deliberately built around that real-world constraint, not a live forecast API — a domain judgment call worth stating explicitly rather than discovering as a bug later ("why does the weather agent return the same thing every time I run it in June?" — because that's correct, not broken).

### 2.3 Why This Chapter Uses a Deterministic, Built-In Lookup Instead of a Real External Climate API

Adding a new external API dependency means a new API key, a new secret in `.env`, and new network flakiness to handle in tests. Since typical/seasonal data changes slowly and doesn't need to be *live*, a small, deterministic, built-in lookup table is a legitimate engineering choice here — not a shortcut taken to avoid real work, but the same YAGNI instinct already applied to `django-filter` in Chapter 6: don't add a dependency the problem doesn't actually require yet. The tool function is written so that swapping in a real provider later touches exactly one function, nothing else — the same "single seam" discipline behind every other external-facing boundary in this project.

---

## 3. Architecture Decision

**Decision:** `GroqClient` gains a new `call_with_tools()` method; the existing `call()` method's signature and behavior are completely unchanged.

**Why:** Chapters 12-13's agents already depend on `call()` and are already tested against it — changing its behavior to accommodate tools would risk regressing two chapters' worth of working code for a capability only this chapter's agent needs. Additive extension, not modification, is the safer path, and is possible here because both methods share a private, retried `_call_raw()` primitive (Section 10.1).

**Decision:** Weather is a **parallel sibling** of Budget in the graph (`travel_planner → {budget_agent, weather_agent} → END`), not chained after Budget.

**Why:** unlike Budget (Chapter 13), which genuinely needs the itinerary's cost estimates, Weather only needs the itinerary's *destinations and dates* — it has no data dependency on Budget's output, and Budget has none on Weather's. Architecture Handbook §9.2 draws this exact parallel-branch shape for precisely this reason: independent computations should run independently, both structurally (in the graph) and, later, potentially concurrently at execution time.

**Decision:** Weather output is written onto **new fields on `ItineraryDay`** (Chapter 8), not a new model.

**Alternative considered:** Create a dedicated `DayWeather` model with its own FK to `ItineraryDay`. **Rejected because:** weather is a simple, single-valued-per-day attribute (one condition, one high, one low, one precipitation chance) — a whole new model with its own migrations, admin, and one-to-one relationship would be structural overhead for data that's naturally just a few extra columns on the day it describes, and Chapter 8's own code comments explicitly reserved this: "a day-level summary, weather forecast — Chapter 14's Weather Agent output lands exactly here."

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Add weather fields to `ItineraryDay` (migration) | Needed before anything can persist weather data |
| Write `ai/tools/weather_tool.py` | Needed before the tool schema/executor can reference it |
| Extend `GroqClient` with `call_with_tools()` | Needed before the agent node can use tool-calling |
| Write `ai/agents/schemas.py` additions (`WeatherForecastSchema`) | Needed before the structuring phase of the agent can validate output |
| Write `ai/agents/weather_agent.py` | Needed before it can be added as a graph node |
| Add the node + parallel edges to `planning_graph.py` | Needed before `ai_agents` sees `weather_forecast` in final state |
| Extend `apps/ai_agents/services.py` with `_persist_weather_forecast` | Last |

---

## 5. File Structure

```
ai/
├── tools/
│   ├── __init__.py
│   └── weather_tool.py            # NEW — get_typical_weather() + its LLM tool schema
├── clients/
│   └── groq_client.py               # MODIFIED — adds call_with_tools()
├── agents/
│   ├── schemas.py                   # MODIFIED — adds WeatherForecastSchema, DailyWeatherSchema
│   └── weather_agent.py              # NEW
├── prompts/
│   └── weather_agent_v1.py            # NEW
└── graphs/
    └── planning_graph.py              # MODIFIED — adds weather_agent as a parallel node

apps/itinerary/
├── models.py                     # MODIFIED — adds weather_* fields to ItineraryDay
└── migrations/
    └── 0002_itineraryday_weather_fields.py   # NEW

apps/ai_agents/
└── services.py                    # MODIFIED — _persist_weather_forecast

ai/tests/
├── test_weather_tool.py            # NEW
├── test_groq_client.py              # MODIFIED — adds call_with_tools tests
├── test_weather_agent.py            # NEW
└── test_planning_graph.py            # MODIFIED — asserts parallel branch structure
```

---

## 6. Folder Location

New/modified files under `ai/` and `apps/itinerary/`, `apps/ai_agents/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations itinerary
docker compose exec web python manage.py migrate

docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.itinerary -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web celery
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations itinerary
Migrations for 'itinerary':
  apps/itinerary/migrations/0002_itineraryday_weather_fields.py
    - Add field weather_condition to itineraryday
    - Add field weather_high_f to itineraryday
    - Add field weather_low_f to itineraryday
    - Add field weather_precipitation_chance to itineraryday

$ docker compose exec web python manage.py shell -c "
from apps.ai_agents import services
from apps.trips.models import Trip
trip = Trip.objects.first()
run = services.run_travel_planner(trip=trip)
day = trip.itinerary_days.first()
print(run.status, day.weather_condition, day.weather_high_f)
"
succeeded partly_cloudy 78.0
```

---

## 10. Code

### 10.1 `ai/clients/groq_client.py` (modified — additive only)

```python
"""
(Chapter 11's groq_client.py, extended additively — call() is
completely unchanged; call_with_tools() is new.)
"""
import json
import logging
from typing import Callable

from groq import Groq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ai.config import AIConfig, load_config
from ai.exceptions import LLMCallFailed

logger = logging.getLogger("ai.clients.groq")


class GroqClient:
    def __init__(self, config: AIConfig | None = None):
        self._config = config or load_config()
        self._client = Groq(api_key=self._config.groq_api_key, timeout=self._config.request_timeout_seconds)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _call_raw(self, *, messages: list[dict], temperature: float, tools: list[dict] | None = None):
        kwargs = {"model": self._config.model_name, "temperature": temperature, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self._client.chat.completions.create(**kwargs)

    def call(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        try:
            response = self._call_raw(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq call failed after retries: %s", exc)
            raise LLMCallFailed(f"LLM call failed after retries: {exc}") from exc

    def call_with_tools(
        self, *, system_prompt: str, user_prompt: str, tools: list[dict],
        tool_executor: Callable[[str, dict], str], temperature: float = 0.2,
    ) -> str:
        """
        Allows the model to call ONE round of tools before answering.
        1. Send the prompt with tool definitions.
        2. If the model requests tool calls, execute each via
           tool_executor(name, arguments) -> str, and feed results back.
        3. Make a final call (no tools offered) to get the answer that
           incorporates the tool results.
        If the model doesn't request any tools, its first response is
        returned directly — no wasted second call.
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            first_response = self._call_raw(messages=messages, temperature=temperature, tools=tools)
            message = first_response.choices[0].message

            if not message.tool_calls:
                return message.content

            messages.append({"role": "assistant", "content": message.content or "", "tool_calls": message.tool_calls})
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                result = tool_executor(name, arguments)
                messages.append({
                    "role": "tool", "tool_call_id": tool_call.id, "name": name, "content": result,
                })

            final_response = self._call_raw(messages=messages, temperature=temperature)
            return final_response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq tool-calling call failed: %s", exc)
            raise LLMCallFailed(f"LLM tool-calling call failed: {exc}") from exc
```

**Why `call_with_tools` handles the "no tool call requested" case by returning immediately, rather than always making two calls**: the model isn't obligated to use a tool just because one is offered — always forcing a second round-trip would waste latency and cost on the (valid) cases where the model already had enough information. This mirrors Chapter 11's `parse_structured_output`'s own instinct: never do more work than the situation actually calls for.

**Why the final call (after tool results are appended) does *not* pass `tools` again**: this prevents an unbounded loop where the model could keep requesting more tool calls indefinitely — Architecture Handbook §9.6 describes "one round" of tool use per agent turn in this project's scope; a genuinely multi-round agentic loop is a meaningfully bigger feature explicitly out of scope here, flagged as a deliberate simplification rather than an oversight.

**Why `_call_raw` is shared between `call()` and `call_with_tools()`**: both need identical retry/backoff behavior (Chapter 11's `tenacity` decorator) and identical low-level request construction — extracting the shared primitive once, rather than duplicating the `@retry`-decorated logic in two places, is the same DRY reasoning behind every other shared-machinery decision so far in this project.

### 10.2 `ai/tools/weather_tool.py`

```python
"""
A deterministic, built-in "typical seasonal weather" lookup — NOT a
live forecast API. See Chapter 14 Theory §2.2-2.3 for why this is
the architecturally correct choice for trips planned months ahead,
and why a built-in table (not a new external dependency) is used
for this first version. Swapping in a real climate-data provider
later only requires changing THIS function's body.
"""
import json

# Deliberately small and approximate — this is placeholder-quality
# seasonal data, not a real climate dataset. Keyed by a coarse
# region guess based on common destination name substrings, with a
# safe default for anything unrecognized.
_SEASONAL_TABLE: dict[str, dict[str, dict]] = {
    "temperate_northern": {
        "December": {"condition": "cold", "high_f": 40, "low_f": 28, "precipitation_chance": 40},
        "June": {"condition": "mild", "high_f": 75, "low_f": 58, "precipitation_chance": 25},
        "default": {"condition": "mild", "high_f": 65, "low_f": 48, "precipitation_chance": 30},
    },
    "tropical": {
        "default": {"condition": "warm_humid", "high_f": 88, "low_f": 74, "precipitation_chance": 55},
    },
    "default": {
        "default": {"condition": "partly_cloudy", "high_f": 70, "low_f": 55, "precipitation_chance": 30},
    },
}

_TROPICAL_HINTS = ("thailand", "bali", "singapore", "philippines", "vietnam")
_TEMPERATE_HINTS = ("japan", "france", "germany", "uk", "united kingdom", "korea")


def _guess_region(destination: str) -> str:
    lowered = destination.lower()
    if any(hint in lowered for hint in _TROPICAL_HINTS):
        return "tropical"
    if any(hint in lowered for hint in _TEMPERATE_HINTS):
        return "temperate_northern"
    return "default"


def get_typical_weather(destination: str, month_name: str) -> dict:
    """
    Returns typical seasonal conditions for a destination in a given
    month. Deterministic (no randomness in the lookup itself) so
    tests and agent behavior are reproducible.
    """
    region = _guess_region(destination)
    region_table = _SEASONAL_TABLE.get(region, _SEASONAL_TABLE["default"])
    return dict(region_table.get(month_name, region_table["default"]))


WEATHER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_typical_weather",
        "description": (
            "Get TYPICAL seasonal weather conditions for a destination "
            "during a given month. This is climatological/seasonal data, "
            "not a live day-specific forecast — appropriate for trips "
            "planned more than two weeks in advance."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string", "description": "Destination name, e.g. 'Tokyo, Japan'"},
                "month_name": {"type": "string", "description": "Full month name, e.g. 'June'"},
            },
            "required": ["destination", "month_name"],
        },
    },
}


def weather_tool_executor(name: str, arguments: dict) -> str:
    """
    The single dispatch point GroqClient.call_with_tools() calls
    into. Currently handles one tool; a dict-based dispatch table
    here (rather than hardcoded if/elif) is what lets Chapter 15/16
    add more tools without restructuring this function's shape.
    """
    handlers = {"get_typical_weather": get_typical_weather}
    handler = handlers.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    result = handler(**arguments)
    return json.dumps(result)
```

**Why `_guess_region` is a crude substring match, explicitly labeled "approximate" in the module docstring**: this is intentionally low-effort, matching the "fake data unblocks development" philosophy from Chapter 10's seed command — the point of this chapter is demonstrating the *tool-calling mechanism* correctly, not building a production-grade climate model. A real provider swap later replaces this whole file's internals without touching any caller.

**Why `weather_tool_executor` always returns a JSON string, even for an unknown tool name**: the tool result is fed straight back into the LLM conversation as message content, which must always be a string — returning an error *as* a string the model can read (`{"error": "..."}`) lets the model potentially recover or explain the issue in its final answer, rather than crashing the whole agent run on an unexpected tool name.

### 10.3 `ai/agents/schemas.py` (addition)

```python
"""
(appended to schemas.py from Chapters 12-13)
"""


class DailyWeatherSchema(BaseModel):
    date: date
    condition: str = Field(..., max_length=50)
    high_f: float
    low_f: float
    precipitation_chance: int = Field(..., ge=0, le=100)

    @field_validator("low_f")
    @classmethod
    def low_must_not_exceed_high(cls, value, info):
        high = info.data.get("high_f")
        if high is not None and value > high:
            raise ValueError("low_f must not exceed high_f")
        return value


class WeatherForecastSchema(BaseModel):
    days: list[DailyWeatherSchema] = Field(..., min_length=1)
```

**Why `precipitation_chance` uses `ge=0, le=100` and `low_f`/`high_f` have a cross-check**: these are the same "catch nonsense before it reaches the database" defense-in-depth instincts from every prior schema in this project (Chapter 12's item bounds, Chapter 13's subtotal check) — a precipitation chance of 150% or a "low" temperature higher than the "high" are exactly the kind of subtly-wrong output an LLM can occasionally produce, and both are now structurally impossible to persist.

### 10.4 `ai/prompts/weather_agent_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT_TOOL_PHASE = """You are a travel weather assistant.
You have access to a get_typical_weather tool that returns TYPICAL
seasonal conditions (not a live forecast) for a destination and month.

For each destination and month mentioned in the trip, call the tool
to gather typical weather conditions. Once you have gathered what
you need, summarize your findings in plain text."""

_SYSTEM_PROMPT_STRUCTURING_PHASE = """You are a data formatting assistant.
Given a plain-text weather summary and a list of specific trip dates,
produce a per-day weather estimate for EACH date listed.

Rules:
- Respond with ONLY valid JSON matching the provided schema.
- Every date listed must appear exactly once in your response.
- Use the seasonal summary provided as the basis for each day's
  estimate — all days in the same month/destination should have
  similar (not necessarily identical) conditions."""


class WeatherAgentPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="weather_agent", version=1, system_prompt=_SYSTEM_PROMPT_TOOL_PHASE)

    def render_user_prompt(self, *, destination_names: list[str], months: list[str]) -> str:
        destinations = ", ".join(destination_names) or "unspecified"
        month_list = ", ".join(sorted(set(months))) or "unspecified"
        return f"Destinations: {destinations}\nMonths covered by this trip: {month_list}"

    def render_structuring_prompt(self, *, weather_summary: str, day_dates: list[str]) -> str:
        dates_list = "\n".join(f"- {d}" for d in day_dates)
        return (
            f"Weather summary:\n{weather_summary}\n\n"
            f"Trip dates requiring an estimate:\n{dates_list}\n\n"
            f"Produce a per-day weather estimate for every date listed above."
        )

    @property
    def structuring_system_prompt(self) -> str:
        return _SYSTEM_PROMPT_STRUCTURING_PHASE
```

**Why this prompt class has two phases (`render_user_prompt` for the tool round, `render_structuring_prompt` + `structuring_system_prompt` for the second round) instead of one**: this mirrors the agent's actual two-call structure (Section 10.5) directly — gathering information via tools is a genuinely different task from formatting that information into strict schema-conformant JSON, and giving each phase its own focused system prompt produces more reliable results than asking one prompt to do both jobs simultaneously.

### 10.5 `ai/agents/weather_agent.py`

```python
"""
The third node in the planning graph, and the first tool-calling
agent. Two-phase: (1) gather typical weather via tool calls, (2)
structure the findings into WeatherForecastSchema for the exact
trip dates.
"""
import datetime

from ai.agents.schemas import WeatherForecastSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import TripPlanningState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.weather_agent_v1 import WeatherAgentPromptV1
from ai.tools.weather_tool import WEATHER_TOOL_SCHEMA, weather_tool_executor

_prompt = WeatherAgentPromptV1()


def _month_name(iso_date: str) -> str:
    return datetime.date.fromisoformat(iso_date).strftime("%B")


def weather_agent_node(state: TripPlanningState, *, client: GroqClient | None = None) -> dict:
    client = client or GroqClient()

    day_dates = [day.date.isoformat() for day in state["itinerary_plan"].days]
    months = [_month_name(d) for d in day_dates]

    tool_phase_prompt = _prompt.render_user_prompt(
        destination_names=state["destination_names"], months=months,
    )
    weather_summary = client.call_with_tools(
        system_prompt=_prompt.system_prompt,
        user_prompt=tool_phase_prompt,
        tools=[WEATHER_TOOL_SCHEMA],
        tool_executor=weather_tool_executor,
        temperature=0.2,
    )

    structuring_prompt = _prompt.render_structuring_prompt(
        weather_summary=weather_summary, day_dates=day_dates,
    )
    forecast: WeatherForecastSchema = parse_structured_output(
        client=client,
        system_prompt=_prompt.structuring_system_prompt,
        user_prompt=structuring_prompt,
        schema=WeatherForecastSchema,
        temperature=0.2,
    )

    return {"weather_forecast": forecast.model_dump()}
```

**Why this node makes up to three LLM calls total (tool round, possible follow-up in `call_with_tools`, plus the structuring round) while Chapters 12-13's agents made only one or two**: tool-calling and structured-output validation are two genuinely separate concerns, each already solved generically (Chapter 11's `parse_structured_output`, this chapter's `call_with_tools`) — composing them for a more complex agent is exactly what those generic building blocks were designed to support, at the cost of more calls (and more latency/cost) for this specific, more complex agent. This trade-off is worth naming: not every agent needs to be this elaborate, and Chapter 15/16's simpler agents will look more like Chapter 13's single-call shape.

### 10.6 `ai/graphs/planning_graph.py` (modified — the graph's shape genuinely changes)

```python
"""
The trip planning graph. THREE nodes now, with a genuine branch:
travel_planner -> {budget_agent, weather_agent} -> END.
"""
from langgraph.graph import END, START, StateGraph

from ai.agents.budget_agent import budget_agent_node
from ai.agents.travel_planner import travel_planner_node
from ai.agents.weather_agent import weather_agent_node
from ai.graphs.state import TripPlanningState


def build_planning_graph():
    graph = StateGraph(TripPlanningState)
    graph.add_node("travel_planner", travel_planner_node)
    graph.add_node("budget_agent", budget_agent_node)
    graph.add_node("weather_agent", weather_agent_node)

    graph.add_edge(START, "travel_planner")
    graph.add_edge("travel_planner", "budget_agent")
    graph.add_edge("travel_planner", "weather_agent")
    graph.add_edge("budget_agent", END)
    graph.add_edge("weather_agent", END)

    return graph.compile()


def run_planning_graph(initial_state: TripPlanningState) -> TripPlanningState:
    compiled_graph = build_planning_graph()
    return compiled_graph.invoke(initial_state)
```

**Why two edges originate from `"travel_planner"` (to `budget_agent` AND to `weather_agent`) instead of one**: this is precisely how LangGraph expresses "these two things can happen independently after this point" — both nodes receive the *same* state (including `itinerary_plan`) once `travel_planner` completes, run without any ordering guarantee relative to each other, and each writes to a different, non-overlapping state key (`budget_estimate` vs `weather_forecast`), so there is no merge conflict to resolve.

### 10.7 `apps/itinerary/models.py` (addition to `ItineraryDay`)

```python
class ItineraryDay(TimeStampedModel):
    # ... existing fields from Chapter 8 unchanged ...

    weather_condition = models.CharField(max_length=50, blank=True)
    weather_high_f = models.FloatField(null=True, blank=True)
    weather_low_f = models.FloatField(null=True, blank=True)
    weather_precipitation_chance = models.PositiveSmallIntegerField(null=True, blank=True)

    # Meta and __str__ unchanged from Chapter 8
```

**Why these fields are all nullable/blank, unlike most fields added in earlier chapters**: an `ItineraryDay` created before this chapter existed (or created without ever running the Weather Agent) has no weather data — these fields must be able to represent "not yet known," which `null=True, blank=True` expresses directly, rather than forcing a meaningless default value onto days that genuinely have no weather estimate yet.

### 10.8 `apps/itinerary/services.py` (addition)

```python
def set_day_weather(*, day: ItineraryDay, condition: str, high_f: float, low_f: float,
                     precipitation_chance: int) -> ItineraryDay:
    day.weather_condition = condition
    day.weather_high_f = high_f
    day.weather_low_f = low_f
    day.weather_precipitation_chance = precipitation_chance
    day.save(update_fields=[
        "weather_condition", "weather_high_f", "weather_low_f",
        "weather_precipitation_chance", "updated_at",
    ])
    return day
```

**Why this is a plain per-day function, with no bulk-write concerns raised here unlike Chapter 13's budget persistence**: no signal in this project currently listens to `ItineraryDay`'s `post_save` — this is worth stating explicitly as a *contrast* to Chapter 13, so the lesson isn't over-generalized into "never use bulk operations anywhere." The rule is specifically "never bypass signals that matter"; here, there simply are none to bypass, so a future `bulk_update()` optimization on this exact function would be perfectly safe if ever needed — flagged as a deliberate, reasoned exception to the pattern, not a contradiction of it.

### 10.9 `apps/ai_agents/services.py` (addition)

```python
def _persist_weather_forecast(*, trip, forecast: dict) -> None:
    days_by_date = {day.date.isoformat(): day for day in trip.itinerary_days.all()}
    for daily in forecast["days"]:
        raw_date = daily["date"]
        date_key = raw_date if isinstance(raw_date, str) else raw_date.isoformat()
        day = days_by_date.get(date_key)
        if day is None:
            continue  # forecast referenced a date with no matching itinerary day — skip defensively
        itinerary_services.set_day_weather(
            day=day, condition=daily["condition"], high_f=daily["high_f"],
            low_f=daily["low_f"], precipitation_chance=daily["precipitation_chance"],
        )
```

**Why `_persist_weather_forecast` silently skips (rather than raising) a forecast date with no matching `ItineraryDay`**: unlike itinerary/budget persistence, where a mismatch would indicate a serious internal bug worth surfacing loudly, a stray weather date is comparatively low-stakes — the itinerary itself is unaffected, only that one day's weather remains unset. Skipping defensively here, rather than failing the entire `AgentRun`, reflects a genuine severity judgment: this chapter treats weather as an enrichment, not a critical dependency of the plan's core validity — worth noting explicitly as a deliberate difference from Chapter 13's stricter, transaction-wrapped budget handling.

This is called from `run_travel_planner`, inside the same `transaction.atomic()` block added in Chapter 13:

```python
with transaction.atomic():
    _persist_itinerary_plan(trip=trip, plan=final_state["itinerary_plan"])
    if final_state.get("budget_estimate"):
        _persist_budget_estimate(trip=trip, estimate=final_state["budget_estimate"])
    if final_state.get("weather_forecast"):
        _persist_weather_forecast(trip=trip, forecast=final_state["weather_forecast"])
```

---

## 11. Code Walkthrough

- **`call_with_tools`'s tool-execution loop is bounded to exactly one round**: this is a scope decision worth restating in the walkthrough, not just the Architecture Decision — a full multi-round ReAct-style agentic loop (where the model can call tools, see results, call more tools, repeatedly) is a meaningfully larger feature. This project's agents each need at most one round of tool-gathering before answering, so the simpler, bounded implementation is both sufficient and safer (no risk of runaway tool-call loops racking up API cost).
- **The graph's parallel branch (Section 10.6) required zero changes to `TripPlanningState`**: this is Chapter 12's forward-sized state paying off for the second time in three chapters — `weather_forecast: dict | None` was already declared, unused, back in Chapter 12.
- **`_guess_region`'s crude heuristic is a visible, labeled placeholder, not a hidden one**: contrast this with how carefully Chapter 6's `Destination.average_daily_cost_usd` or Chapter 9's real cost data were treated — this chapter is explicit that weather quality is intentionally approximate, so nobody mistakes this for production-grade climate data later.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `AttributeError: 'NoneType' object has no attribute 'tool_calls'` | Testing `call_with_tools` against a mock that doesn't shape its fake response like a real Groq tool-calling response | Ensure test mocks set `message.tool_calls` to either `None` or a list of mock tool-call objects with `.function.name`/`.function.arguments`/`.id` |
| Weather data never appears on any `ItineraryDay` | `forecast["days"]` dates don't match any `ItineraryDay.date` in the trip (e.g., date format mismatch) | Confirm both sides use ISO date strings consistently; check the defensive skip in `_persist_weather_forecast` isn't silently swallowing a real bug — add temporary logging if needed |
| `ValueError: low_f must not exceed high_f` (wrapped in `StructuredOutputInvalid` after retry) | Model produced physically nonsensical output, even after correction | Expected occasional occurrence — the schema validator is working correctly |
| Two LLM calls happen even when the model didn't need the tool | Misreading `call_with_tools`'s early-return path | Check `message.tool_calls` is actually falsy in that case — if tools genuinely weren't needed, only one call should occur; verify via call-count assertions in a test |

---

## 13. Debugging

```bash
# 1. Exercise the weather tool directly, no LLM involved at all
docker compose exec web python manage.py shell -c "
from ai.tools.weather_tool import get_typical_weather
print(get_typical_weather('Tokyo, Japan', 'June'))
print(get_typical_weather('Bangkok, Thailand', 'August'))
"

# 2. Confirm the graph's parallel structure directly
docker compose exec web python manage.py shell -c "
from ai.graphs.planning_graph import build_planning_graph
graph = build_planning_graph()
edges = {(e.source, e.target) for e in graph.get_graph().edges}
print(('travel_planner', 'budget_agent') in edges)
print(('travel_planner', 'weather_agent') in edges)
"
```

**Rollback strategy:** identical to Chapters 12-13 — `transaction.atomic()` already covers this chapter's new persistence call, so a failure anywhere in the three-part persistence (itinerary, budget, weather) leaves the trip exactly as it was before the run.

---

## 14. Testing

### 14.1 `ai/tests/test_weather_tool.py`

```python
import json

from ai.tools.weather_tool import get_typical_weather, weather_tool_executor


def test_get_typical_weather_returns_expected_shape():
    result = get_typical_weather("Tokyo, Japan", "June")
    assert set(result.keys()) == {"condition", "high_f", "low_f", "precipitation_chance"}


def test_tropical_hint_routes_to_tropical_table():
    result = get_typical_weather("Bangkok, Thailand", "August")
    assert result["condition"] == "warm_humid"


def test_unknown_destination_falls_back_to_default():
    result = get_typical_weather("Nowhereland", "March")
    assert result["condition"] == "partly_cloudy"


def test_lookup_is_deterministic():
    first = get_typical_weather("Tokyo, Japan", "June")
    second = get_typical_weather("Tokyo, Japan", "June")
    assert first == second


def test_weather_tool_executor_returns_json_string():
    result = weather_tool_executor("get_typical_weather", {"destination": "Tokyo, Japan", "month_name": "June"})
    parsed = json.loads(result)
    assert "condition" in parsed


def test_weather_tool_executor_handles_unknown_tool():
    result = weather_tool_executor("nonexistent_tool", {})
    parsed = json.loads(result)
    assert "error" in parsed
```

### 14.2 `ai/tests/test_groq_client.py` (additions)

```python
import json
from unittest.mock import MagicMock, patch

from ai.clients.groq_client import GroqClient


def _tool_call_response(tool_name: str, arguments: dict, call_id: str = "call_1"):
    response = MagicMock()
    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)
    response.choices = [MagicMock(message=MagicMock(content=None, tool_calls=[tool_call]))]
    return response


def _plain_response(content: str):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content, tool_calls=None))]
    return response


@patch("ai.clients.groq_client.Groq")
def test_call_with_tools_skips_second_call_when_no_tool_requested(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _plain_response("no tool needed")

    client = GroqClient(config=fake_config)
    result = client.call_with_tools(
        system_prompt="sys", user_prompt="user", tools=[{"type": "function"}],
        tool_executor=lambda name, args: "unused",
    )

    assert result == "no tool needed"
    assert mock_instance.chat.completions.create.call_count == 1


@patch("ai.clients.groq_client.Groq")
def test_call_with_tools_executes_tool_and_makes_final_call(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = [
        _tool_call_response("get_typical_weather", {"destination": "Tokyo", "month_name": "June"}),
        _plain_response("Tokyo in June is typically mild."),
    ]

    executed = {}

    def fake_executor(name, args):
        executed["name"] = name
        executed["args"] = args
        return '{"condition": "mild"}'

    client = GroqClient(config=fake_config)
    result = client.call_with_tools(
        system_prompt="sys", user_prompt="user",
        tools=[{"type": "function"}], tool_executor=fake_executor,
    )

    assert result == "Tokyo in June is typically mild."
    assert executed["name"] == "get_typical_weather"
    assert mock_instance.chat.completions.create.call_count == 2
```

### 14.3 `ai/tests/test_weather_agent.py`

```python
from unittest.mock import MagicMock

from ai.agents.schemas import ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema
from ai.agents.weather_agent import weather_agent_node


def test_weather_agent_node_returns_forecast_for_each_day():
    fake_client = MagicMock()
    fake_client.call_with_tools.return_value = "Tokyo in June: mild, occasional rain."
    fake_client.call.return_value = (
        '{"days": [{"date": "2026-06-01", "condition": "mild", "high_f": 75, '
        '"low_f": 60, "precipitation_chance": 30}]}'
    )

    state = {
        "itinerary_plan": ItineraryPlanSchema(days=[
            ItineraryDaySchema(day_number=1, date="2026-06-01", items=[
                ItineraryItemSchema(title="Arrive")
            ])
        ]),
        "destination_names": ["Tokyo, Japan"],
    }

    result = weather_agent_node(state, client=fake_client)

    assert "weather_forecast" in result
    assert result["weather_forecast"]["days"][0]["condition"] == "mild"
    fake_client.call_with_tools.assert_called_once()
```

### 14.4 `ai/tests/test_planning_graph.py` (additions)

```python
def test_graph_has_parallel_branch_from_travel_planner():
    from ai.graphs.planning_graph import build_planning_graph
    graph = build_planning_graph()
    edges = {(e.source, e.target) for e in graph.get_graph().edges}
    assert ("travel_planner", "budget_agent") in edges
    assert ("travel_planner", "weather_agent") in edges
    # budget_agent and weather_agent must NOT depend on each other
    assert ("budget_agent", "weather_agent") not in edges
    assert ("weather_agent", "budget_agent") not in edges
```

### 14.5 `apps/ai_agents/tests/test_services.py` (additions)

```python
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents import services
from apps.trips.models import Trip
from ai.agents.schemas import (
    DailyWeatherSchema, ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema,
    WeatherForecastSchema,
)

User = get_user_model()


class WeatherPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="w@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1),
        )

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_weather_persisted_onto_correct_day(self, mock_graph):
        mock_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                    ItineraryItemSchema(title="Arrive")
                ])
            ]),
            "weather_forecast": WeatherForecastSchema(days=[
                DailyWeatherSchema(date=date(2026, 6, 1), condition="sunny", high_f=80, low_f=65, precipitation_chance=10)
            ]).model_dump(),
        }

        services.run_travel_planner(trip=self.trip)

        day = self.trip.itinerary_days.get(day_number=1)
        self.assertEqual(day.weather_condition, "sunny")
        self.assertEqual(day.weather_high_f, 80)

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_missing_weather_forecast_does_not_break_run(self, mock_graph):
        mock_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                    ItineraryItemSchema(title="Arrive")
                ])
            ]),
            # no weather_forecast key at all
        }
        agent_run = services.run_travel_planner(trip=self.trip)
        self.assertEqual(agent_run.status, "succeeded")
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.ai_agents apps.itinerary -v 2
```

---

## 15. Git Commit

```bash
git add ai/tools/ ai/clients/groq_client.py ai/agents/ ai/prompts/weather_agent_v1.py ai/graphs/planning_graph.py apps/itinerary/models.py apps/itinerary/migrations/ apps/itinerary/services.py apps/ai_agents/services.py ai/tests/
git commit -m "feat(ai_agents): Weather Agent — first tool-calling agent, first parallel graph branch

- GroqClient.call_with_tools(): additive extension, call() completely
  unchanged; shared _call_raw() primitive keeps retry/backoff
  consistent across both plain and tool-enabled calls; bounded to one
  tool round (no unbounded agentic loop) — deliberate scope limit
- weather_tool.py: deterministic, built-in seasonal lookup, NOT a live
  forecast — architecturally correct for trips planned months ahead
  (see Chapter 14 Theory); real provider swap touches only this file
- WeatherForecastSchema/DailyWeatherSchema: precipitation 0-100 bound,
  low_f <= high_f cross-check — same defense-in-depth instinct as
  every prior schema
- planning_graph.py: travel_planner now fans out to BOTH budget_agent
  AND weather_agent in parallel (two edges from one source) — first
  time the graph's shape genuinely branches, not just extends;
  required ZERO changes to TripPlanningState (Chapter 12 pre-sizing
  paying off again)
- ItineraryDay gains nullable weather_* fields per Chapter 8's own
  reserved comment; set_day_weather() uses plain per-day writes,
  explicitly noted as safe (no signals listen to ItineraryDay,
  unlike Chapter 13's BudgetLineItem caution) — contrast documented,
  not just applied
- _persist_weather_forecast defensively skips unmatched dates rather
  than failing the whole run — weather treated as enrichment, not
  critical path, a documented severity judgment distinct from budget

Chapter 14 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `GroqClient.call()` behavior/signature completely unchanged; only additive `call_with_tools()` added
- [ ] `call_with_tools` skips the second LLM call when no tool was requested — verified by call-count assertion
- [ ] `get_typical_weather` is deterministic (same input → same output), tested explicitly
- [ ] `WeatherForecastSchema` rejects `low_f > high_f` and out-of-range `precipitation_chance`
- [ ] Graph edges confirm `travel_planner` fans out to both `budget_agent` and `weather_agent`, with **no** edge between the two siblings themselves
- [ ] `ItineraryDay.weather_*` fields are nullable; migration applied cleanly
- [ ] `set_day_weather` uses simple per-day writes; the "no signals here, unlike budget" contrast is documented, not just implicit
- [ ] `_persist_weather_forecast` skips (doesn't crash) on an unmatched date
- [ ] All tests passing across `ai/tests`, `apps.ai_agents`, `apps.itinerary`
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 15 — Recommendation Agent** is the first agent to consume **two** upstream nodes' output at once — both the itinerary (Chapter 12) and the weather forecast (this chapter) — writing into Chapter 10's `Recommendation` model for the first time since it was built as an empty data layer. This is also where the graph's parallel branches (Budget, Weather) converge again into a shared downstream dependency, requiring LangGraph to wait for **both** parallel branches to complete before the Recommendation node can run — the first real join point in the graph's shape. Say **"Continue to Chapter 15"** when ready.
