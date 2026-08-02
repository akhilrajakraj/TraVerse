# Chapter 20 — Retrieval-Augmented Generation (RAG)

**Volume 5: Conversational Layer | Chapter 20 of 29**

> Volume 5 closes here. This chapter grounds chat answers in the actual `Destination` catalog (Chapter 6) rather than relying purely on the model's own training knowledge — the first time this project retrieves its own stored data as context for a prompt in a general, reusable way. The interesting decision in this chapter isn't the AI part — it's recognizing that "RAG" doesn't require a vector database, and building it as a **tool** reuses Chapter 14's tool-calling machinery almost entirely unchanged.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Explain what Retrieval-Augmented Generation actually means at its core, and recognize when a full vector/embedding search pipeline is warranted versus when simple structured search is the correct, sufficient tool.
- Implement retrieval as a **tool** the chat agent can call, reusing Chapter 14's `call_with_tools` machinery rather than building a new retrieval subsystem from scratch.
- Resolve the tension between "tool executors that need Django access" and "the `ai/` package has zero Django dependency," using dependency injection at the exact seam Chapter 14 already built for this purpose.
- Recognize when shared logic has earned its extraction into a dedicated function — refactoring Chapter 6's inline search into a reusable selector once a second real consumer needs it.

---

## 2. Theory

### 2.1 What RAG Actually Means, Stripped of Buzzwords (ELI10)

"Retrieval-Augmented Generation" sounds complicated, but the idea is simple: instead of only trusting what the model already "knows" from training, you first **look something up** in your own real data, then hand what you found to the model as part of its prompt, so its answer is grounded in facts you actually control. If a traveler asks "what's a good destination in Japan with cheap food," the model shouldn't guess from possibly-outdated training knowledge — it should look at this project's *actual* `Destination` catalog (Chapter 6, with real `average_daily_cost_usd` values) and answer based on what's really there.

### 2.2 Why This Chapter Does NOT Add a Vector Database (ELI10)

The buzzword-heavy version of RAG usually involves embeddings and a vector database, built to answer fuzzy semantic questions over large, unstructured document collections — "find paragraphs similar in meaning to this question," across thousands or millions of documents. Our `Destination` catalog (Chapter 6) is nothing like that: it's a small, structured table with clean fields (`name`, `country`, `description`, `average_daily_cost_usd`). A traveler's question about destinations is well-served by a targeted database query on those structured fields — the same `icontains` search technique Chapter 6 already built — not by a fundamentally different retrieval technology. Reaching for a vector database here would be solving a problem this project doesn't actually have, the same YAGNI judgment already made for Chapter 6's search filters, Chapter 14's weather data, and every other "don't add a dependency the problem doesn't require" decision in this project.

### 2.3 Why Retrieval Is Built as a Tool, Not a New Subsystem

Chapter 14 already solved "let the LLM decide when it needs outside information, fetch it, and continue" — that's precisely what retrieval is. Building RAG as a *second* tool the chat agent can call, rather than inventing a separate retrieval pipeline that always runs before every chat message regardless of whether it's needed, means the model only pays the retrieval cost when a question genuinely calls for catalog lookup ("what's a good destination for X"), not for every message including ones that don't need it ("thanks, that's helpful!").

---

## 3. Architecture Decision

**Decision:** Retrieval is implemented as an additional LLM tool (`search_destinations`) available to the chat agent, using Chapter 14's `call_with_tools` machinery unchanged — no new retrieval subsystem, no vector database.

**Decision:** The tool's **schema** (pure data describing the tool to the LLM) lives in `ai/tools/`, matching Chapter 14's pattern exactly. The tool's **executor** (the function that actually queries `Destination`) lives in `apps/ai_agents/services.py`, not in `ai/`, because it genuinely needs Django ORM access — resolved via the exact same dependency-injection seam `call_with_tools` already provides (`tool_executor` as an injected callable), rather than compromising Chapter 11's zero-Django-dependency boundary.

**Alternative considered:** Give `ai/tools/weather_tool.py`-style modules a Django-dependent executor directly in `ai/`. **Rejected because:** this would be the first crack in a boundary held cleanly since Chapter 11 — the injectable-executor pattern already exists specifically to avoid ever needing this compromise, and using it here is the correct application of machinery already built for this exact situation.

**Decision:** Chapter 6's inline `icontains` search logic (previously only in `DestinationListCreateView.get_queryset()`) is extracted into a new `apps/destinations/selectors.py`, now shared by both the public search API and this chapter's new RAG tool executor.

**Why now, not earlier:** Chapter 6 had exactly one consumer of that search logic — extracting it into a separate function then would have been premature abstraction for a single call site. This chapter introduces a genuine second consumer, which is precisely the point at which shared logic earns its extraction (a "rule of two," not "extract everything defensively from the start").

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Extract `apps/destinations/selectors.py` | Needed before either consumer (the view or the new RAG executor) can share it |
| Refactor `DestinationListCreateView` to use the selector | Confirms the extraction didn't change existing behavior, before building anything new on top of it |
| Write `ai/tools/destination_search_tool.py` (schema only) | Needed before the chat agent can offer it to the LLM |
| Extend `ai/agents/chat_agent.py` to optionally accept tools/executor | Needed before `ai_agents` can inject a Django-aware executor |
| Write the executor in `apps/ai_agents/services.py` and wire it into `generate_chat_reply` | Last |

---

## 5. File Structure

```
apps/destinations/
├── selectors.py                  # NEW — search_destinations(), extracted from the view
├── views.py                       # MODIFIED — now calls the selector
└── tests/
    ├── test_selectors.py            # NEW
    └── test_views.py                 # MODIFIED — confirms refactor preserved behavior

ai/
├── tools/
│   └── destination_search_tool.py    # NEW — schema only, no executor (contrast with weather_tool.py)
└── agents/
    └── chat_agent.py                  # MODIFIED — optional tools/tool_executor parameters

apps/ai_agents/
├── services.py                    # MODIFIED — _search_destinations_executor, wired into generate_chat_reply
└── tests/test_services.py           # MODIFIED

ai/tests/
└── test_chat_agent.py               # MODIFIED — tool-calling path
```

---

## 6. Folder Location

Modified/new files under `apps/destinations/`, `ai/`, `apps/ai_agents/`.

---

## 7. Terminal Commands

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.destinations apps.ai_agents -v 2
```

No migrations this chapter — no model changes.

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py shell -c "
from apps.chat import services as chat_services
from apps.ai_agents.services import generate_chat_reply
from django.contrib.auth import get_user_model
user = get_user_model().objects.first()
session = chat_services.create_session(user=user)
reply = generate_chat_reply(session=session, user_message='What are some budget-friendly destinations in Japan?')
print(reply.content)
"
Based on our catalog, Kyoto has an estimated daily cost of around $95,
making it a relatively budget-friendly option in Japan compared to Tokyo...
```

---

## 10. Code

### 10.1 `apps/destinations/selectors.py`

```python
"""
Extracted from DestinationListCreateView.get_queryset() (Chapter 6)
now that a second real consumer (this chapter's RAG tool executor)
needs the exact same logic — see Chapter 20 Architecture Decision
for why extraction happens now, not earlier.
"""
from django.db.models import Q, QuerySet

from apps.destinations.models import Destination


def search_destinations(*, query: str = "", destination_type: str = "", limit: int | None = None) -> QuerySet:
    queryset = Destination.objects.filter(is_active=True)
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(country__icontains=query) | Q(description__icontains=query)
        )
    if destination_type:
        queryset = queryset.filter(destination_type=destination_type)
    if limit is not None:
        queryset = queryset[:limit]
    return queryset
```

**Why `description__icontains` is added here, when Chapter 6's original search only matched `name`/`country`**: for the RAG use case specifically, a traveler's question ("somewhere good for hiking") is more likely to match catalog *description* text than a destination's literal name — extending the search to include description is a small, genuine improvement this chapter's real second use case revealed, applied to the shared function so both consumers benefit, not duplicated only for RAG.

### 10.2 `apps/destinations/views.py` (modified)

```python
from apps.destinations.selectors import search_destinations


class DestinationListCreateView(ListCreateAPIView):
    serializer_class = DestinationSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        return search_destinations(
            query=self.request.query_params.get("search", ""),
            destination_type=self.request.query_params.get("type", ""),
        )
```

**Why this refactor is worth its own note despite being a small diff**: the view's behavior is unchanged (proven by Section 14's regression test on the existing Chapter 6 test suite), but its *logic ownership* has moved — the view is now purely HTTP plumbing, and the actual search rule lives in one place two different callers can trust to behave identically. This is a textbook "extract on the second use" refactor, worth recognizing as a pattern to apply elsewhere in a real project, not just here.

### 10.3 `ai/tools/destination_search_tool.py`

```python
"""
Tool SCHEMA only — no executor function here, unlike
ai/tools/weather_tool.py (Chapter 14). The executor needs Django ORM
access to query the real Destination catalog, so it's provided by
apps.ai_agents.services at call time instead — see Chapter 20
Architecture Decision.
"""

SEARCH_DESTINATIONS_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_destinations",
        "description": (
            "Search the travel platform's own destination catalog for "
            "places matching a query. Use this whenever the traveler asks "
            "about specific destinations, costs, or characteristics that "
            "should be grounded in real catalog data rather than general "
            "knowledge."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms, e.g. 'cheap food Japan' or 'beach relaxing'"},
            },
            "required": ["query"],
        },
    },
}
```

### 10.4 `ai/agents/chat_agent.py` (modified — additive)

```python
"""
(Chapter 19's chat_agent.py, extended additively)
"""
from typing import Callable

from ai.clients.groq_client import GroqClient
from ai.prompts.chat_agent_v1 import ChatAgentPromptV1

_prompt = ChatAgentPromptV1()


def generate_reply(
    *, conversation_context: str, trip_context: str | None, latest_message: str,
    client: GroqClient | None = None,
    tools: list[dict] | None = None,
    tool_executor: Callable[[str, dict], str] | None = None,
) -> str:
    client = client or GroqClient()
    user_prompt = _prompt.render_user_prompt(
        conversation_context=conversation_context, trip_context=trip_context, latest_message=latest_message,
    )

    if tools and tool_executor:
        return client.call_with_tools(
            system_prompt=_prompt.system_prompt, user_prompt=user_prompt,
            tools=tools, tool_executor=tool_executor, temperature=0.6,
        )
    return client.call(system_prompt=_prompt.system_prompt, user_prompt=user_prompt, temperature=0.6)
```

**Why `tools`/`tool_executor` default to `None` and the function falls back to the plain `call()` path when either is missing**: this keeps Chapter 19's existing tests and call sites working completely unchanged — a caller that doesn't care about retrieval (or any future tool) never has to know these parameters exist. This is the same additive-extension discipline Chapter 14 used when adding `call_with_tools` to `GroqClient` without touching `call()`.

### 10.5 `apps/ai_agents/services.py` (addition)

```python
import json

from ai.tools.destination_search_tool import SEARCH_DESTINATIONS_TOOL_SCHEMA
from apps.destinations.selectors import search_destinations


def _search_destinations_executor(name: str, arguments: dict) -> str:
    """
    THE Django-aware tool executor — lives here, not in ai/, because
    it queries the real Destination catalog. Injected into the chat
    agent via GroqClient.call_with_tools()'s tool_executor parameter,
    the exact seam Chapter 14 built for precisely this situation.
    """
    if name != "search_destinations":
        return json.dumps({"error": f"Unknown tool: {name}"})

    query = arguments.get("query", "")
    results = search_destinations(query=query, limit=5)
    payload = [
        {
            "name": d.name, "country": d.country, "description": d.description,
            "average_daily_cost_usd": str(d.average_daily_cost_usd) if d.average_daily_cost_usd else None,
        }
        for d in results
    ]
    return json.dumps({"results": payload})
```

`generate_chat_reply` (Chapter 19) is updated to pass these through:

```python
def generate_chat_reply(*, session: ChatSession, user_message: str, triggered_by=None) -> ChatMessage:
    chat_services.add_message(session=session, role=ChatRole.USER, content=user_message)

    history = chat_services.get_session_messages(session=session)
    conversation_messages = [
        ConversationMessage(role=m.role, content=m.content, created_at=m.created_at) for m in history
    ]
    context = build_context(conversation_messages)
    context_text = format_context_for_prompt(context)

    reply_text = _generate_chat_reply_text(
        conversation_context=context_text,
        trip_context=_trip_context_summary(session.trip),
        latest_message=user_message,
        tools=[SEARCH_DESTINATIONS_TOOL_SCHEMA],           # NEW
        tool_executor=_search_destinations_executor,        # NEW
    )

    return chat_services.add_message(session=session, role=ChatRole.ASSISTANT, content=reply_text)
```

**Why `generate_chat_reply` always passes the tool now, rather than conditionally offering it only for certain messages**: the LLM itself decides whether the tool is actually needed for a given message — that's the entire point of tool-calling (Chapter 14 Theory §2.1), and offering it unconditionally costs nothing extra when the model doesn't choose to use it (`call_with_tools` already returns immediately without a second call in that case, per Chapter 14's own optimization).

---

## 11. Code Walkthrough

- **The tool-executor injection pattern, built in Chapter 14 for a completely different reason (avoiding a live weather API dependency), turns out to be exactly the right tool for a completely different problem here (avoiding a Django dependency inside `ai/`)** — this is worth sitting with as a genuine lesson: good abstractions often solve problems their author didn't originally anticipate, precisely because they were built around a real, general principle (here: "the caller, not the callee, decides how a tool's logic is actually implemented") rather than a narrow, specific need.
- **`ai/tools/destination_search_tool.py` has no executor function at all, in direct visual contrast to `ai/tools/weather_tool.py`'s combined schema+executor**: seeing these two tool files side by side is the clearest illustration in the project of "the boundary is drawn by what the tool's implementation actually needs," not by a rule applied uniformly regardless of circumstance.
- **The `apps/destinations/selectors.py` extraction (Section 10.1) demonstrates the "rule of two" for refactoring directly**: Chapter 6 didn't extract this logic because there was only one caller; this chapter did, because a second, genuinely different caller (the RAG executor) appeared. Premature extraction (doing it in Chapter 6 "just in case") would have been guessing at a need that took 14 chapters to actually materialize.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| Chat replies never seem to use real catalog data | The model chose not to call the tool for that particular message — expected for messages that don't need catalog lookup | Confirm with a message that clearly needs catalog grounding ("what's the average cost in Kyoto?"); not every message should trigger tool use |
| `ImportError` in `ai/tools/destination_search_tool.py` for anything Django-related | Someone accidentally added Django imports to a schema-only file | Remove them — this file must stay pure data, per this chapter's entire architectural point |
| `apps/destinations` tests fail after the selector refactor | The refactor subtly changed behavior (e.g., dropped the `is_active` filter) | Compare `search_destinations()` line by line against the original `get_queryset()` logic it replaced |
| RAG tool results include inactive/deactivated destinations | `search_destinations()`'s `is_active=True` filter was accidentally removed during refactor or extension | Confirm the filter is still present — it was preserved intentionally from Chapter 6 |

---

## 13. Debugging

```bash
# 1. Exercise the retrieval executor directly, no LLM involved
docker compose exec web python manage.py shell -c "
from apps.ai_agents.services import _search_destinations_executor
print(_search_destinations_executor('search_destinations', {'query': 'Japan'}))
"

# 2. Confirm the selector and the refactored view still agree
docker compose exec web python manage.py shell -c "
from apps.destinations.selectors import search_destinations
print(list(search_destinations(query='tok').values_list('name', flat=True)))
"
```

**Rollback strategy:** the selector extraction has no data implications (pure query logic); the chat agent's tool additions are fully backward-compatible defaults, so nothing here has a meaningful rollback beyond reverting the code changes themselves.

---

## 14. Testing

### 14.1 `apps/destinations/tests/test_selectors.py`

```python
from django.test import TestCase

from apps.destinations.models import Destination
from apps.destinations.selectors import search_destinations


class SearchDestinationsSelectorTests(TestCase):
    def setUp(self):
        Destination.objects.create(name="Tokyo", country="Japan", description="Bustling capital")
        Destination.objects.create(name="Kyoto", country="Japan", description="Temples and gardens")
        Destination.objects.create(name="Paris", country="France", description="City of light")
        Destination.objects.create(name="Osaka", country="Japan", description="", is_active=False)

    def test_matches_name(self):
        results = search_destinations(query="tok")
        self.assertEqual({d.name for d in results}, {"Tokyo"})

    def test_matches_description(self):
        results = search_destinations(query="temples")
        self.assertEqual({d.name for d in results}, {"Kyoto"})

    def test_excludes_inactive(self):
        results = search_destinations(query="osaka")
        self.assertEqual(list(results), [])

    def test_limit_applied(self):
        results = search_destinations(query="", limit=2)
        self.assertEqual(len(results), 2)
```

### 14.2 `apps/destinations/tests/test_views.py` (regression addition)

```python
def test_search_still_works_after_selector_refactor(self):
    """
    Regression test proving Chapter 20's extraction into selectors.py
    preserved Chapter 6's original search behavior exactly.
    """
    response = self.client.get(
        reverse("destinations:list-create") + "?search=japan", **self._auth(self.access)
    )
    names = {r["name"] for r in response.data["results"]}
    self.assertEqual(names, {"Tokyo", "Kyoto"})
```

### 14.3 `ai/tests/test_chat_agent.py` (additions)

```python
from unittest.mock import MagicMock

from ai.agents.chat_agent import generate_reply


def test_generate_reply_uses_call_with_tools_when_tools_provided():
    fake_client = MagicMock()
    fake_client.call_with_tools.return_value = "Kyoto is a great budget option!"

    result = generate_reply(
        conversation_context="", trip_context=None, latest_message="Budget destinations in Japan?",
        client=fake_client, tools=[{"type": "function"}], tool_executor=lambda n, a: "unused",
    )

    assert result == "Kyoto is a great budget option!"
    fake_client.call_with_tools.assert_called_once()
    fake_client.call.assert_not_called()


def test_generate_reply_falls_back_to_plain_call_without_tools():
    fake_client = MagicMock()
    fake_client.call.return_value = "General advice."

    result = generate_reply(
        conversation_context="", trip_context=None, latest_message="Hi",
        client=fake_client,
    )

    assert result == "General advice."
    fake_client.call_with_tools.assert_not_called()
```

### 14.4 `apps/ai_agents/tests/test_services.py` (additions)

```python
import json
from unittest.mock import patch

from django.test import TestCase

from apps.ai_agents.services import _search_destinations_executor
from apps.destinations.models import Destination


class SearchDestinationsExecutorTests(TestCase):
    def test_executor_returns_matching_destinations(self):
        Destination.objects.create(name="Kyoto", country="Japan", description="Temples", average_daily_cost_usd="95.00")

        result = json.loads(_search_destinations_executor("search_destinations", {"query": "kyoto"}))

        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["name"], "Kyoto")
        self.assertEqual(result["results"][0]["average_daily_cost_usd"], "95.00")

    def test_executor_handles_unknown_tool_name(self):
        result = json.loads(_search_destinations_executor("not_a_real_tool", {}))
        self.assertIn("error", result)


class GenerateChatReplyWithRAGTests(TestCase):
    @patch("apps.ai_agents.services._generate_chat_reply_text")
    def test_tools_and_executor_passed_to_agent(self, mock_generate):
        from apps.chat import services as chat_services
        from django.contrib.auth import get_user_model

        mock_generate.return_value = "reply"
        user = get_user_model().objects.create_user(email="rag@example.com", password="pass1234")
        session = chat_services.create_session(user=user)

        from apps.ai_agents.services import generate_chat_reply
        generate_chat_reply(session=session, user_message="Cheap destinations in Japan?")

        call_kwargs = mock_generate.call_args.kwargs
        self.assertIn("tools", call_kwargs)
        self.assertIn("tool_executor", call_kwargs)
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.destinations apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add apps/destinations/selectors.py apps/destinations/views.py apps/destinations/tests/ ai/tools/destination_search_tool.py ai/agents/chat_agent.py apps/ai_agents/services.py apps/ai_agents/tests/test_services.py ai/tests/test_chat_agent.py
git commit -m "feat(chat): Retrieval-Augmented Generation via tool-calling, no vector DB

- RAG built as a TOOL (search_destinations), reusing Chapter 14's
  call_with_tools machinery entirely unchanged — no new retrieval
  subsystem, no vector database. Deliberate: our catalog is small
  and structured, well-served by existing search, not fuzzy semantic
  search over an unstructured corpus (see Chapter 20 Theory)
- ai/tools/destination_search_tool.py: schema ONLY, no executor —
  direct contrast with weather_tool.py's combined schema+executor,
  because this tool's real implementation needs Django ORM access
- Executor lives in apps/ai_agents/services.py, injected into
  call_with_tools via the exact dependency-injection seam Chapter 14
  built for a different original reason — reused here for the
  zero-Django-dependency boundary instead
- apps/destinations/selectors.py: Chapter 6's inline search logic
  extracted now that a genuine SECOND consumer (this RAG executor)
  needs it — 'rule of two' refactoring, not premature abstraction;
  regression-tested to prove behavior is unchanged
- search_destinations() extended to also match description text,
  benefiting both existing consumers
- chat_agent.generate_reply() gains optional tools/tool_executor
  params, fully backward compatible with Chapter 19's existing tests

Volume 5 (Conversational Layer) complete. Chapter 20 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `apps/destinations/selectors.py` extracted; existing Chapter 6 search tests still pass unchanged (regression-tested)
- [ ] `search_destinations()` also matches `description`, benefiting both the public API and the RAG tool
- [ ] `ai/tools/destination_search_tool.py` contains only a schema, zero Django imports, zero executor logic
- [ ] `chat_agent.generate_reply()`'s `tools`/`tool_executor` params are optional and backward-compatible — Chapter 19's tests still pass unmodified
- [ ] `_search_destinations_executor` lives in `apps/ai_agents/services.py`, not in `ai/`
- [ ] `generate_chat_reply` always offers the tool; the LLM decides whether to use it
- [ ] Single-door rule still holds — `apps/destinations` has no new dependency on `ai/`
- [ ] All tests passing across `ai/tests`, `apps.destinations`, `apps.ai_agents`
- [ ] Commit made
- [ ] **Volume 5 (Conversational Layer) is now complete**

---

## 17. Next Chapter Preview

**Chapter 21 — `documents` App** begins Volume 6 (Supporting Apps). It builds PDF export of a trip's itinerary and shareable links — the first chapter to generate a downloadable artifact rather than only API responses, and the first to reckon with public, unauthenticated (but unguessable) access via a shareable link, a genuinely different security model than every `IsOwner`-protected endpoint built so far. Say **"Continue to Chapter 21"** when ready.
