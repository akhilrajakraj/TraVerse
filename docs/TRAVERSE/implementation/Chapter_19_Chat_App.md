# Chapter 19 — `chat` App

**Volume 5: Conversational Layer | Chapter 19 of 29**

> Chapter 18's pure transformation layer finally gets a real caller. This chapter builds `ChatSession`/`ChatMessage` (a genuine Django app, persisting real conversation history), a new single-call chat agent in `ai/`, and the bridge between them — routed exclusively through `ai_agents`, per Chapter 12's single-door rule. This chapter also introduces the project's first genuinely **bidirectional** app dependency: `chat` calls into `ai_agents` for replies, and `ai_agents` calls into `chat` to read and write messages — a deliberate, documented exception to the otherwise one-directional dependency graph established back in Architecture Handbook §4.3.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Model a session/message conversation structure, and decide correctly when a foreign key should be optional (a chat session may or may not be scoped to a trip).
- Wire Chapter 18's `build_context()` into a real Django data flow: fetch rows, convert to `ConversationMessage`, transform, format, prompt.
- Recognize and justify a bidirectional dependency between two apps as a deliberate exception, not an architectural violation, when one of those apps is the designated orchestration hub.
- Decide when an AI-touched interaction is lightweight enough to handle synchronously in the request/response cycle, versus needing Celery's async dispatch pattern from Chapter 12.

---

## 2. Theory

### 2.1 Why Chat Sessions Are Optionally, Not Always, Linked to a Trip (ELI10)

Sometimes a traveler wants to ask "what's a good carry-on backpack?" without that question being about any specific trip they've planned. Other times they want to ask "should I move my museum visit to day 3?" which only makes sense in the context of one specific trip's itinerary. Making `ChatSession.trip` nullable, rather than required, lets both kinds of conversation exist in the same model — general-purpose assistant chat and trip-grounded chat are the same *mechanism*, differing only in whether trip context gets woven into the prompt.

### 2.2 Why This Is the First Bidirectional App Dependency in the Project

Every app dependency so far has flowed one direction: `ai_agents` reaches into `trips`, `itinerary`, `budget`, `recommendations` to read/write their data (Chapters 12-16), but none of those apps ever call back into `ai_agents`. `chat` breaks that pattern *by design* — a user sends a message through `chat`'s own API, and `chat` needs `ai_agents` to actually generate a reply (since `chat`, like every other domain app, is never allowed to import from `ai/` directly). This is fine specifically because `ai_agents` is not a peer domain app — it's the designated orchestration hub, and being called *by* other apps for AI work is exactly its job, symmetric with it calling *into* other apps to persist AI-generated results. The one-directional rule was about isolating raw AI access, not about preventing any app from asking the orchestrator for help.

### 2.3 Why Chat Replies Are Synchronous, Not Dispatched Through Celery Like `/plan/`

Architecture Handbook §2.4's reasoning for async dispatch was specific: an LLM call taking 5-30 seconds shouldn't block a Gunicorn worker, and the five-agent planning graph (Chapters 12-17) could take meaningfully longer than that. A single chat reply is one LLM call — typically a few seconds, well within a normal HTTP request's timeout budget, and users expect a chat interface to respond in the same request, not to poll for a reply the way `/plan/`'s heavier operation requires. This chapter makes a genuinely different, documented choice for a genuinely different situation, rather than mechanically reusing the async pattern everywhere.

---

## 3. Architecture Decision

**Decision:** `ChatSession.trip` is `on_delete=SET_NULL`, nullable — a session survives its linked trip's deletion, degrading to a general (trip-less) conversation rather than being destroyed.

**Decision:** `chat` and `ai_agents` have a bidirectional dependency: `chat`'s views call `apps.ai_agents.services.generate_chat_reply()`; `ai_agents.services` calls `apps.chat.services` to read/write messages. Documented explicitly as acceptable because `ai_agents` is the orchestration hub, not a peer domain app — the one-directional rule (Architecture Handbook §4.3) governs relationships *between domain apps*, not between a domain app and the orchestrator whose entire purpose is being called into.

**Decision:** `generate_chat_reply()` runs synchronously inside the request/response cycle, with no Celery dispatch and no `AgentRun` row created.

**Trade-off documented:** unlike the planning graph, individual chat turns are not logged as `AgentRun`s — creating one row per chat message would be noisy at a much higher frequency than planning runs, and Chapter 24's analytics can be revisited later with a lighter-weight, chat-specific logging strategy if that need becomes concrete. This is flagged as a deliberate scope decision, not an oversight.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `ChatSession`/`ChatMessage` models | Needed before any service or view can exist |
| Write `apps/chat/services.py` | Needed before `ai_agents` can call into it |
| Write `ai/prompts/chat_agent_v1.py` and `ai/agents/chat_agent.py` | Needed before `ai_agents`'s bridge function can call them |
| Write `apps/ai_agents/services.generate_chat_reply` | Needed before `chat`'s views can call it |
| Write `chat`'s views/serializers/urls | Last |

---

## 5. File Structure

```
apps/chat/
├── __init__.py
├── apps.py
├── models.py                    # ChatSession, ChatMessage
├── services.py                   # create_session, add_message, get_session_messages
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py

ai/
├── prompts/
│   └── chat_agent_v1.py            # NEW
└── agents/
    └── chat_agent.py                # NEW

apps/ai_agents/
├── services.py                    # MODIFIED — generate_chat_reply
└── tests/test_services.py           # MODIFIED

ai/tests/
└── test_chat_agent.py               # NEW
```

---

## 6. Folder Location

New app files under `apps/chat/` (already scaffolded empty since Chapter 2). New `ai/` files under `ai/prompts/` and `ai/agents/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations chat
docker compose exec web python manage.py migrate

docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.chat apps.ai_agents -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

No Celery restart needed this chapter — chat replies deliberately don't go through Celery (Section 2.3).

---

## 9. Expected Output

```
$ curl -X POST http://localhost:8000/api/v1/chat/sessions/ -H "Authorization: Bearer <access>" -d '{"trip_id": "<uuid>"}'
{"id": "a1b2...", "trip": "<uuid>", "title": ""}

$ curl -X POST http://localhost:8000/api/v1/chat/sessions/a1b2.../messages/ \
  -H "Authorization: Bearer <access>" -d '{"content": "What should I pack for the weather?"}'
{"id": 2, "role": "assistant", "content": "Based on the mild June weather expected for your trip, I'd recommend..."}
```

---

## 10. Code

### 10.1 `apps/chat/models.py`

```python
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class ChatRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class ChatSession(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    A conversation thread. Optionally scoped to a Trip — see Chapter
    19 Theory §2.1 for why this is nullable rather than required.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions")
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_sessions",
        help_text="Optional. SET_NULL — deleting a trip degrades this to a "
                   "general conversation rather than destroying chat history.",
    )
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"

    def __str__(self) -> str:
        return f"ChatSession<{self.user.email}>"


class ChatMessage(TimeStampedModel):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ChatRole.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["session", "created_at"])]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:50]}"
```

**Why `ChatSession` uses `UUIDPrimaryKeyModel` like `Trip` (Chapter 7), while `ChatMessage` uses a plain integer PK like `ItineraryItem` (Chapter 8)**: sessions are the unit addressed in a personal, potentially-shareable URL; individual messages are always accessed *through* a session, never independently — the exact same distinction Chapter 7 drew for `Trip` versus `Destination`, applied here.

**Why `ChatMessage.Meta.ordering = ["created_at"]` (ascending), unlike almost every other model in this project (`["-created_at"]`, newest-first)**: a conversation reads naturally in chronological order, oldest-first — this is the one model where the project's usual "newest first" default (established back in Chapter 3's `TimeStampedModel`) is deliberately overridden, because it would otherwise produce a conversation transcript in reverse.

### 10.2 `apps/chat/services.py`

```python
from apps.chat.models import ChatMessage, ChatRole, ChatSession


def create_session(*, user, trip=None, title: str = "") -> ChatSession:
    return ChatSession.objects.create(user=user, trip=trip, title=title)


def add_message(*, session: ChatSession, role: str, content: str) -> ChatMessage:
    return ChatMessage.objects.create(session=session, role=role, content=content)


def get_session_messages(*, session: ChatSession) -> list[ChatMessage]:
    return list(session.messages.all())
```

### 10.3 `ai/prompts/chat_agent_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a friendly, knowledgeable AI travel planning assistant.
Answer the traveler's questions helpfully and concisely.

If trip context is provided, ground your answers in the specifics
of that trip — its dates, destinations, itinerary, and budget —
rather than giving generic advice. If no trip context is provided,
answer as a general travel assistant."""


class ChatAgentPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="chat_agent", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(self, *, conversation_context: str, trip_context: str | None,
                            latest_message: str) -> str:
        parts = []
        if trip_context:
            parts.append(f"Trip context:\n{trip_context}")
        if conversation_context:
            parts.append(f"Conversation so far:\n{conversation_context}")
        parts.append(f"Traveler's latest message:\n{latest_message}")
        return "\n\n".join(parts)
```

### 10.4 `ai/agents/chat_agent.py`

```python
"""
The chat agent — a single LLM call, no schema validation, no
LangGraph node. Chat replies are free-form conversational text, the
same reasoning Chapter 18 gave for the memory summarizer's plain-
text output: there's no bounded shape to validate prose against.
"""
from ai.clients.groq_client import GroqClient
from ai.prompts.chat_agent_v1 import ChatAgentPromptV1

_prompt = ChatAgentPromptV1()


def generate_reply(*, conversation_context: str, trip_context: str | None,
                    latest_message: str, client: GroqClient | None = None) -> str:
    client = client or GroqClient()
    user_prompt = _prompt.render_user_prompt(
        conversation_context=conversation_context, trip_context=trip_context, latest_message=latest_message,
    )
    return client.call(system_prompt=_prompt.system_prompt, user_prompt=user_prompt, temperature=0.6)
```

**Why `temperature=0.6`, meaningfully higher than every planning-graph agent (0.2-0.4)**: chat is the only agent in this project whose output is meant to feel natural and conversational, not structurally consistent — there's no schema for a higher temperature to accidentally break, so this is the one place the trade-off (more varied phrasing, at the cost of *slightly* less predictable output) is worth making deliberately.

### 10.5 `apps/ai_agents/services.py` (addition)

```python
from ai.agents.chat_agent import generate_reply as _generate_chat_reply_text
from ai.memory.conversation_memory import build_context, format_context_for_prompt
from ai.memory.message import ConversationMessage
from apps.chat import services as chat_services
from apps.chat.models import ChatMessage, ChatRole, ChatSession


def _trip_context_summary(trip) -> str | None:
    if trip is None:
        return None
    lines = [f"Trip: {trip.title} ({trip.start_date} to {trip.end_date})"]
    for day in trip.itinerary_days.all()[:14]:
        titles = ", ".join(item.title for item in day.items.all())
        if titles:
            lines.append(f"Day {day.day_number}: {titles}")
    return "\n".join(lines)


def generate_chat_reply(*, session: ChatSession, user_message: str, triggered_by=None) -> ChatMessage:
    """
    THE bridge for chat. Note the bidirectional dependency this
    creates with apps.chat — see Chapter 19 Architecture Decision
    for why this is a deliberate, documented exception to the
    otherwise one-directional app dependency graph.

    Deliberately synchronous — no Celery dispatch, no AgentRun row.
    See Chapter 19 Theory §2.3.
    """
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
    )

    return chat_services.add_message(session=session, role=ChatRole.ASSISTANT, content=reply_text)
```

**Why the user's message is persisted (`chat_services.add_message(role=USER, ...)`) *before* the LLM is called, not after**: if the LLM call fails partway through, the user's own message should still be saved — losing what someone actually typed because of a downstream failure would be a genuinely bad experience; only the *assistant's* reply is contingent on the call succeeding.

**Why `_trip_context_summary` caps itinerary days at `[:14]`**: a defensive bound against an unusually long trip flooding the chat prompt with itinerary detail — matching the same "don't let one input balloon the prompt" instinct behind Chapter 18's token-budget windowing, applied here as a simple slice rather than a full token-aware trim, since trip context is a secondary input, not the primary conversation itself.

### 10.6 `apps/chat/serializers.py`

```python
from rest_framework import serializers

from apps.chat.models import ChatMessage, ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "trip", "title", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = fields


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)
```

### 10.7 `apps/chat/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import ChatMessage, ChatSession
from apps.chat.serializers import ChatMessageSerializer, ChatSessionSerializer, SendMessageSerializer
from apps.trips.models import Trip


class ChatSessionListCreateView(ListCreateAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        trip = None
        trip_id = request.data.get("trip")
        if trip_id:
            trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

        from apps.chat import services as chat_services
        session = chat_services.create_session(user=request.user, trip=trip, title=request.data.get("title", ""))
        return Response(ChatSessionSerializer(session).data, status=http_status.HTTP_201_CREATED)


class ChatMessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_pk):
        session = get_object_or_404(ChatSession, pk=session_pk, user=request.user)
        return Response(ChatMessageSerializer(session.messages.all(), many=True).data)


class SendChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_pk):
        session = get_object_or_404(ChatSession, pk=session_pk, user=request.user)
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.ai_agents.services import generate_chat_reply
        reply = generate_chat_reply(
            session=session, user_message=serializer.validated_data["content"], triggered_by=request.user,
        )
        return Response(ChatMessageSerializer(reply).data, status=http_status.HTTP_201_CREATED)
```

**Why `create_session`/`generate_chat_reply` are imported *inside* their view methods, not at the top of the file**: this is the same defensive pattern Chapter 12's Celery task used, applied here specifically because of Section 2.2's bidirectional dependency — `apps.ai_agents.services` imports `apps.chat.services`/`apps.chat.models` at its own module level, so importing `apps.ai_agents.services` back at `apps.chat.views`'s module level (which Django loads very early, via URL configuration) risks a genuine import-order problem during Django's app-loading sequence. Deferring the import until the view method actually runs — well after all apps have finished loading — sidesteps this cleanly, the same reasoning already given for Celery tasks in Chapter 12.

### 10.8 `apps/chat/urls.py`

```python
from django.urls import path

from apps.chat.views import ChatMessageListView, ChatSessionListCreateView, SendChatMessageView

app_name = "chat"

urlpatterns = [
    path("sessions/", ChatSessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<uuid:session_pk>/messages/", ChatMessageListView.as_view(), name="message-list"),
    path("sessions/<uuid:session_pk>/messages/send/", SendChatMessageView.as_view(), name="message-send"),
]
```

**Why `GET .../messages/` and `POST .../messages/send/` are separate endpoints rather than one endpoint handling both `GET` (list) and `POST` (send + reply)**: a `POST` to a "messages" collection endpoint conventionally means "create a message," which is ambiguous here — does it mean "store my message" or "store my message AND generate a reply"? A distinct `.../send/` endpoint makes the actual behavior (send, and receive a reply, as one atomic user-facing action) unambiguous — matching the "explicit over generic" convention used throughout this project since Chapter 7's `/status/` endpoint.

### 10.9 `config/urls.py` (addition)

```python
path("api/v1/chat/", include("apps.chat.urls")),
```

### 10.10 `apps/chat/admin.py`

```python
from django.contrib import admin

from apps.chat.models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ["role", "content", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "trip", "title", "created_at"]
    search_fields = ["user__email", "title"]
    inlines = [ChatMessageInline]
```

---

## 11. Code Walkthrough

- **The bidirectional dependency (Section 3) is visible directly in the imports**: `apps/ai_agents/services.py` imports `apps.chat.services`/`apps.chat.models`; `apps/chat/views.py` imports `apps.ai_agents.services` (deferred, inside the method). Seeing both directions explicitly, rather than one hidden behind an interface, is intentional — the dependency is real and should be visible, not obscured.
- **`generate_chat_reply` reuses Chapter 18's `build_context`/`format_context_for_prompt` completely unmodified** — no changes were needed to either function to plug in a real Django data source; they were designed from the start to accept plain `ConversationMessage` objects regardless of where they came from, exactly the payoff of building that layer with zero Django dependency in the first place.
- **This chapter is the first to make a genuinely different async-vs-sync decision than every prior AI-triggering endpoint**: worth reinforcing that "always use Celery for anything AI-related" was never actually the rule — the real rule (Architecture Handbook §2.4) was about protecting Gunicorn workers from *long* blocking calls, and a single chat turn doesn't meet that bar the way a five-agent graph run does.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `ImportError` / circular import when starting Django | `apps.ai_agents.services` and `apps.chat.views` both imported at module level in a way that creates a real cycle | Confirm the deferred, in-method import pattern from Section 10.7 is used in `chat`'s views |
| A trip-scoped chat session shows generic advice, ignoring trip details | `session.trip` is `None` (either never set, or set-to-null after trip deletion) | Expected if the trip was deleted (Section 3's documented `SET_NULL` behavior) — otherwise confirm `trip_id` was actually passed on session creation |
| `403`/`404` when trying to create a session with someone else's `trip_id` | Correct behavior — `get_object_or_404(Trip, pk=trip_id, user=request.user)` in `ChatSessionListCreateView.create` | This is intentional ownership enforcement, not a bug |
| Chat replies feel slow (several seconds) | Expected — a single real LLM call typically takes a few seconds; this is why Section 2.3 stayed synchronous rather than needing Celery, not a performance regression |

---

## 13. Debugging

```bash
# 1. Exercise the whole chat pipeline manually, real LLM call
docker compose exec web python manage.py shell -c "
from apps.chat import services as chat_services
from apps.ai_agents.services import generate_chat_reply
from django.contrib.auth import get_user_model
user = get_user_model().objects.first()
session = chat_services.create_session(user=user)
reply = generate_chat_reply(session=session, user_message='What should I pack for a rainy trip?')
print(reply.content)
"

# 2. Confirm message ordering is chronological, not newest-first
docker compose exec web python manage.py shell -c "
from apps.chat.models import ChatSession
session = ChatSession.objects.first()
print([m.role for m in session.messages.all()])
"
```

**Rollback strategy:** `ChatMessage` rows are simple, append-only records with no signals or derived state depending on them — deleting a bad session (`session.delete()`, cascading to its messages) is always a safe, complete reset.

---

## 14. Testing

### 14.1 `ai/tests/test_chat_agent.py`

```python
from unittest.mock import MagicMock

from ai.agents.chat_agent import generate_reply


def test_generate_reply_calls_client_with_correct_prompt_parts():
    fake_client = MagicMock()
    fake_client.call.return_value = "Pack a light rain jacket!"

    result = generate_reply(
        conversation_context="user: Hi\nassistant: Hello!",
        trip_context="Trip: Japan (2026-06-01 to 2026-06-05)",
        latest_message="What should I pack?",
        client=fake_client,
    )

    assert result == "Pack a light rain jacket!"
    call_kwargs = fake_client.call.call_args.kwargs
    assert "Japan" in call_kwargs["user_prompt"]
    assert "What should I pack?" in call_kwargs["user_prompt"]


def test_generate_reply_handles_missing_trip_context():
    fake_client = MagicMock()
    fake_client.call.return_value = "General travel advice here."

    result = generate_reply(
        conversation_context="", trip_context=None, latest_message="Any tips for solo travel?",
        client=fake_client,
    )
    assert result == "General travel advice here."
```

### 14.2 `apps/chat/tests/test_services.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.chat import services
from apps.chat.models import ChatRole
from apps.trips.models import Trip

User = get_user_model()


class ChatServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="c@example.com", password="pass1234")

    def test_create_session_without_trip(self):
        session = services.create_session(user=self.user)
        self.assertIsNone(session.trip)

    def test_create_session_with_trip(self):
        trip = Trip.objects.create(user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        session = services.create_session(user=self.user, trip=trip)
        self.assertEqual(session.trip, trip)

    def test_add_message_and_get_session_messages_in_order(self):
        session = services.create_session(user=self.user)
        services.add_message(session=session, role=ChatRole.USER, content="First")
        services.add_message(session=session, role=ChatRole.ASSISTANT, content="Second")
        messages = services.get_session_messages(session=session)
        self.assertEqual([m.content for m in messages], ["First", "Second"])

    def test_session_survives_trip_deletion(self):
        trip = Trip.objects.create(user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        session = services.create_session(user=self.user, trip=trip)
        trip.delete()
        session.refresh_from_db()
        self.assertIsNone(session.trip)
```

### 14.3 `apps/ai_agents/tests/test_services.py` (addition)

```python
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents.services import generate_chat_reply
from apps.chat import services as chat_services
from apps.chat.models import ChatMessage, ChatRole

User = get_user_model()


class GenerateChatReplyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="chat@example.com", password="pass1234")
        self.session = chat_services.create_session(user=self.user)

    @patch("apps.ai_agents.services._generate_chat_reply_text")
    def test_user_message_persisted_before_reply(self, mock_generate):
        mock_generate.return_value = "Here's my advice!"
        generate_chat_reply(session=self.session, user_message="What's a good packing list?")

        messages = list(self.session.messages.all())
        self.assertEqual(messages[0].role, ChatRole.USER)
        self.assertEqual(messages[0].content, "What's a good packing list?")
        self.assertEqual(messages[1].role, ChatRole.ASSISTANT)
        self.assertEqual(messages[1].content, "Here's my advice!")

    @patch("apps.ai_agents.services._generate_chat_reply_text")
    def test_no_agent_run_created_for_chat(self, mock_generate):
        mock_generate.return_value = "reply"
        from apps.ai_agents.models import AgentRun
        generate_chat_reply(session=self.session, user_message="Hi")
        self.assertEqual(AgentRun.objects.count(), 0)

    @patch("apps.ai_agents.services._generate_chat_reply_text")
    def test_user_message_persisted_even_if_reply_generation_fails(self, mock_generate):
        mock_generate.side_effect = RuntimeError("provider down")
        with self.assertRaises(RuntimeError):
            generate_chat_reply(session=self.session, user_message="Will this survive?")

        self.assertTrue(ChatMessage.objects.filter(session=self.session, role=ChatRole.USER).exists())
```

### 14.4 `apps/chat/tests/test_views.py`

```python
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

User = get_user_model()


class ChatViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="v@example.com", password="pass1234")
        login = self.client.post(reverse("accounts:login"), {"email": "v@example.com", "password": "pass1234"})
        self.token = login.data["tokens"]["access"]

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_create_session_without_trip(self):
        response = self.client.post(reverse("chat:session-list-create"), {}, **self._auth())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("apps.ai_agents.services._generate_chat_reply_text")
    def test_send_message_returns_assistant_reply(self, mock_generate):
        mock_generate.return_value = "Sure, here's some advice!"
        session_response = self.client.post(reverse("chat:session-list-create"), {}, **self._auth())
        session_id = session_response.data["id"]

        response = self.client.post(
            reverse("chat:message-send", kwargs={"session_pk": session_id}),
            {"content": "Any tips?"}, **self._auth(),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "assistant")
        self.assertEqual(response.data["content"], "Sure, here's some advice!")

    def test_cannot_read_another_users_session_messages(self):
        other = User.objects.create_user(email="other@example.com", password="pass1234")
        from apps.chat import services as chat_services
        other_session = chat_services.create_session(user=other)

        response = self.client.get(
            reverse("chat:message-list", kwargs={"session_pk": other_session.pk}), **self._auth()
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.chat apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add apps/chat/ ai/agents/chat_agent.py ai/prompts/chat_agent_v1.py apps/ai_agents/services.py config/urls.py ai/tests/test_chat_agent.py
git commit -m "feat(chat): chat app + chat-to-agent bridge

- ChatSession (UUID PK, like Trip)/ChatMessage (int PK, like
  ItineraryItem) — trip FK nullable/SET_NULL, general vs trip-scoped
  conversations share one mechanism
- ChatMessage.Meta.ordering is ASCENDING (chronological) — the one
  deliberate exception to the project's usual newest-first default
- ai/agents/chat_agent.py: single LLM call, no schema (free-form
  prose, same reasoning as Chapter 18's summarizer), temperature=0.6
  (highest in the project — no schema to break, natural phrasing
  is the goal here)
- generate_chat_reply() bridges chat <-> ai/, reusing Chapter 18's
  build_context()/format_context_for_prompt() completely unmodified
- FIRST bidirectional app dependency in the project: chat calls INTO
  ai_agents (for replies), ai_agents calls INTO chat (for message
  persistence) — documented explicitly as acceptable because
  ai_agents is the orchestration hub, not a peer domain app
- Deliberately synchronous (no Celery, no AgentRun row) — a single
  chat turn doesn't meet Architecture Handbook §2.4's bar for async
  dispatch the way the 5-agent planning graph does
- User's message persisted BEFORE the LLM call, so it survives even
  if reply generation fails — tested explicitly
- Deferred (in-method) imports in chat/views.py specifically to avoid
  the bidirectional dependency causing an app-loading-order issue

Chapter 19 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `ChatSession.trip` is nullable, `SET_NULL` — session survives trip deletion, tested explicitly
- [ ] `ChatMessage.Meta.ordering` is ascending, documented as the deliberate exception to the project default
- [ ] `ai/agents/chat_agent.py` makes exactly one LLM call, no Pydantic schema involved
- [ ] Bidirectional `chat` ↔ `ai_agents` dependency is documented as intentional, not accidental
- [ ] `generate_chat_reply` is synchronous — no Celery task, no `AgentRun` row — both verified by tests
- [ ] User's message survives a simulated reply-generation failure — tested explicitly
- [ ] Cross-user session access returns 404
- [ ] All tests passing across `ai/tests`, `apps.chat`, `apps.ai_agents`
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 20 — Retrieval-Augmented Generation (RAG)** closes Volume 5. It extends the chat agent (and potentially the Recommendation Agent) with the ability to ground answers in the actual `Destination` catalog (Chapter 6) rather than relying purely on the model's own training knowledge — the first time this project retrieves *our own stored data* as context for a prompt in a general, reusable way, rather than the narrowly-scoped trip data already threaded through every prior agent. Say **"Continue to Chapter 20"** when ready.
