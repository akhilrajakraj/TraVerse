# Chapter 18 — Memory & Conversation State

**Volume 5: Conversational Layer | Chapter 18 of 29**

> Volume 5 begins. Everything in Volume 4 ran once per trigger, with no memory of anything beyond what got persisted to a `Trip`. This chapter builds the pure-Python transformation logic Chapter 19's `chat` app will need to hold a genuine back-and-forth conversation: turning a growing list of messages into a compact, prompt-ready context window, with automatic summarization when the conversation gets long. Like every other `ai/` chapter, this one persists nothing to Postgres — that's Chapter 19's job. This chapter only builds the machinery that transforms already-fetched messages into something worth sending to an LLM.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Explain why a rough, approximate token estimate is an acceptable engineering choice here, and when it would stop being acceptable.
- Build a "recency window" selection strategy that always preserves chronological order and never returns an empty context, even for a single oversized message.
- Recognize when summarization is worth the cost of an extra LLM call, and implement a threshold that avoids re-summarizing on every single turn.
- Understand exactly where this chapter's responsibility ends and Chapter 19's begins — a transformation layer with no persistence of its own.

---

## 2. Theory

### 2.1 Why Conversation History Can't Just Be Sent to the LLM In Full Every Time (ELI10)

Imagine a friend who, every time you say one new sentence to them, insists on first re-reading your entire conversation history out loud before responding — including things from an hour ago that don't matter anymore. That's wasteful and slow. Architecture Handbook §9.5 already stated the fix: "persist memory in Postgres and only inject a relevant, summarized slice per call." This chapter builds exactly that "relevant, summarized slice" — a **recency window** (the most recent messages, kept in full) plus, when the conversation has grown long enough, a **summary** of everything older than that window.

### 2.2 Why an Approximate Token Estimate, Not a Real Tokenizer (ELI10)

Counting exactly how many "tokens" (the units an LLM actually processes) a piece of text uses requires either calling the provider's API or running a real tokenizer library matched to that specific model. For the purpose this chapter needs — deciding roughly how many recent messages fit in a budget, and roughly when a conversation has grown "long" — an approximation (about 4 characters per token for English text, a widely-used rule of thumb) is accurate enough to make good decisions, without adding a new dependency. This is the same YAGNI judgment already made for Chapter 14's weather data and Chapter 6's search: solve the problem with the simplest tool that's actually good enough, and name the limitation explicitly rather than hide it.

### 2.3 Why Summarization Has Its Own, Higher Threshold Instead of Triggering the Moment the Recency Window Overflows

If summarization triggered the instant a conversation exceeded the recency window's budget, nearly every multi-turn conversation would trigger an extra, costly LLM call on almost every single turn — wasteful, and not meaningfully more useful than just trimming older messages outright for a conversation that's only slightly over budget. Giving summarization its own, meaningfully higher trigger threshold means it only kicks in for conversations that have grown genuinely long, where a summary actually earns its cost by preserving real information that would otherwise be silently dropped.

---

## 3. Architecture Decision

**Decision:** Token estimation is a simple character-count heuristic (`len(text) // 4`), not a real tokenizer library.

**Trade-off documented:** this estimate can be meaningfully wrong for non-English text or unusual formatting (code blocks, for instance, tokenize very differently from prose) — acceptable here because the consequence of being wrong is only a slightly-too-generous or slightly-too-conservative context window, never a correctness bug; if token *precision* ever becomes genuinely important (e.g., hitting real provider context-limit errors in production), this is the one function to swap for a real tokenizer, with zero changes needed anywhere else in this module.

**Decision:** `select_recent_window` always keeps at least the single most recent message, even if that one message alone exceeds the token budget.

**Why:** returning an empty context because the most recent message happens to be long would be actively worse than slightly exceeding the intended budget — the most recent message is, by definition, the most relevant thing to respond to.

**Decision:** `build_context` recomputes the summary from scratch every time summarization is needed, rather than incrementally updating a stored, evolving summary.

**Alternative considered:** Cache a running summary and only summarize the *newly*-overflowed messages each time, appending to the existing summary. **Rejected for this version because:** unlike Chapter 15's Recommendation accept/reject state (a genuine user decision worth preserving across regeneration), a conversation summary has no equivalent "decision" to protect — recomputing it fresh each time is simpler, cannot drift or compound errors from prior summarization passes, and the extra LLM call cost is bounded by the deliberately-high trigger threshold from Section 2.3. Flagged here as a legitimate future optimization, not a hidden limitation.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `ConversationMessage` | Needed before any function can operate on messages |
| Define `estimate_tokens`/`estimate_message_tokens` | Needed before window selection or summarization triggers can make any decision |
| Define `select_recent_window` | Needed before `build_context` can assemble anything |
| Define `ai/prompts/memory_summarizer_v1.py` and `summarize_older_messages` | Needed before `build_context` can handle the long-conversation case |
| Define `build_context`/`format_context_for_prompt` | Last — the public entry point Chapter 19 will actually call |

---

## 5. File Structure

```
ai/
├── memory/
│   ├── __init__.py                 # already existed, empty, since Chapter 11
│   ├── message.py                    # NEW — ConversationMessage
│   ├── token_estimator.py             # NEW
│   └── conversation_memory.py          # NEW — select_recent_window, build_context, etc.
└── prompts/
    └── memory_summarizer_v1.py         # NEW

ai/tests/
├── test_token_estimator.py            # NEW
└── test_conversation_memory.py         # NEW
```

No Django app files are touched this chapter — a deliberate contrast to Chapter 17's heavy Django-side work, and the same "pure `ai/` package" scope as Chapter 11.

---

## 6. Folder Location

All new files under `ai/memory/` and `ai/prompts/`.

---

## 7. Terminal Commands

```bash
docker compose exec web pytest ai/tests -v
```

No migrations, no `manage.py test` — this chapter has zero Django surface area.

---

## 8. Docker Commands

None required beyond the standard test run — no settings, no signals, no new dependencies this chapter.

---

## 9. Expected Output

```
$ docker compose exec web pytest ai/tests/test_conversation_memory.py ai/tests/test_token_estimator.py -v
test_conversation_memory.py::test_short_conversation_skips_summarization PASSED
test_conversation_memory.py::test_long_conversation_triggers_summarization PASSED
test_conversation_memory.py::test_recent_window_always_keeps_most_recent_message PASSED
test_conversation_memory.py::test_recent_window_preserves_chronological_order PASSED
test_token_estimator.py::test_estimate_tokens_roughly_matches_char_count_heuristic PASSED
========================== 5 passed in 0.05s ==========================
```

---

## 10. Code

### 10.1 `ai/memory/message.py`

```python
"""
Plain representation of one conversation turn. NOT a Django model —
Chapter 19's chat app will have its own ChatMessage model and is
responsible for converting its rows into these before calling
anything in this module.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConversationMessage:
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime | None = None
```

**Why this is a plain `dataclass`, not a Pydantic `BaseModel` like every schema in `ai/agents/schemas.py`**: those schemas exist specifically to *validate untrusted LLM output* — that's Pydantic's job in this project. `ConversationMessage` represents *our own* already-known-good data (either a user's real chat input or an LLM's own already-successful prior response) — there's nothing to validate, so a lighter-weight dataclass is the right tool, not a reflexive "always use Pydantic" habit.

### 10.2 `ai/memory/token_estimator.py`

```python
"""
Rough, approximate token estimation. NOT a real tokenizer — see
Chapter 18 Theory §2.2 for why this is an acceptable, deliberate
choice, and what would need to change if real precision ever became
necessary.
"""
from ai.memory.message import ConversationMessage

_CHARS_PER_TOKEN_ESTIMATE = 4
_PER_MESSAGE_OVERHEAD_TOKENS = 4  # accounts for role/formatting overhead in a real prompt


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN_ESTIMATE)


def estimate_message_tokens(message: ConversationMessage) -> int:
    return estimate_tokens(message.content) + _PER_MESSAGE_OVERHEAD_TOKENS
```

### 10.3 `ai/prompts/memory_summarizer_v1.py`

```python
from ai.prompts.base import PromptTemplate

_SYSTEM_PROMPT = """You are a conversation summarization assistant.
Given an earlier portion of a conversation between a traveler and a
trip-planning assistant, produce a concise summary that preserves
any concrete facts, preferences, or decisions mentioned — dates,
budget constraints, destinations, likes/dislikes, anything the
assistant would need to continue the conversation naturally.

Do not include commentary about the summarization task itself.
Output only the summary."""


class MemorySummarizerPromptV1(PromptTemplate):
    def __init__(self):
        super().__init__(name="memory_summarizer", version=1, system_prompt=_SYSTEM_PROMPT)

    def render_user_prompt(self, *, transcript: str) -> str:
        return f"Conversation transcript to summarize:\n\n{transcript}"
```

**Why this prompt's output is plain text, not validated through a Pydantic schema like every agent in `ai/agents/`**: a summary is free-form prose by nature — there's no meaningful structure to validate it against the way an itinerary or budget estimate has bounded, typed fields. Chapter 11's `parse_structured_output` machinery exists for exactly the cases that *do* have a target shape; forcing a schema onto free text here would add ceremony without adding safety.

### 10.4 `ai/memory/conversation_memory.py`

```python
"""
The core transformation layer: raw message history in, a compact,
prompt-ready context out. Persists NOTHING — Chapter 19's chat app
owns storage; this module is a pure function library operating on
whatever messages it's handed.
"""
from ai.clients.groq_client import GroqClient
from ai.memory.message import ConversationMessage
from ai.memory.token_estimator import estimate_message_tokens
from ai.prompts.memory_summarizer_v1 import MemorySummarizerPromptV1

RECENCY_WINDOW_TOKENS = 1500
SUMMARIZATION_TRIGGER_TOKENS = 3000

_prompt = MemorySummarizerPromptV1()


def total_tokens(messages: list[ConversationMessage]) -> int:
    return sum(estimate_message_tokens(m) for m in messages)


def select_recent_window(
    messages: list[ConversationMessage], max_tokens: int = RECENCY_WINDOW_TOKENS,
) -> list[ConversationMessage]:
    """
    Walks messages newest-first, keeping as many as fit within
    max_tokens, then returns them in original chronological order.
    Always keeps at least the single most recent message — see
    Chapter 18 Architecture Decision.
    """
    kept: list[ConversationMessage] = []
    budget = max_tokens
    for message in reversed(messages):
        cost = estimate_message_tokens(message)
        if cost > budget and kept:
            break
        kept.append(message)
        budget -= cost
    kept.reverse()
    return kept


def needs_summarization(
    messages: list[ConversationMessage], trigger_tokens: int = SUMMARIZATION_TRIGGER_TOKENS,
) -> bool:
    return total_tokens(messages) > trigger_tokens


def summarize_older_messages(
    older_messages: list[ConversationMessage], *, client: GroqClient | None = None,
) -> str:
    if not older_messages:
        return ""
    client = client or GroqClient()
    transcript = "\n".join(f"{m.role}: {m.content}" for m in older_messages)
    return client.call(
        system_prompt=_prompt.system_prompt,
        user_prompt=_prompt.render_user_prompt(transcript=transcript),
        temperature=0.2,
    )


def build_context(
    messages: list[ConversationMessage], *, client: GroqClient | None = None,
    recency_window_tokens: int = RECENCY_WINDOW_TOKENS,
    trigger_tokens: int = SUMMARIZATION_TRIGGER_TOKENS,
) -> dict:
    """
    The public entry point. Returns:
        {"summary": str | None, "recent_messages": list[ConversationMessage]}

    If the full history already fits comfortably, no summarization
    call is made at all — the same "don't do more work than the
    situation needs" instinct as Chapter 11's parse_structured_output
    and Chapter 14's call_with_tools.
    """
    if not needs_summarization(messages, trigger_tokens):
        return {"summary": None, "recent_messages": select_recent_window(messages, recency_window_tokens)}

    recent = select_recent_window(messages, recency_window_tokens)
    recent_ids = {id(m) for m in recent}
    older = [m for m in messages if id(m) not in recent_ids]

    summary = summarize_older_messages(older, client=client)
    return {"summary": summary, "recent_messages": recent}


def format_context_for_prompt(context: dict) -> str:
    """
    Flattens the dict from build_context() into a single string
    block ready to drop into any agent's user prompt.
    """
    parts = []
    if context.get("summary"):
        parts.append(f"[Earlier conversation summary]\n{context['summary']}")
    for message in context["recent_messages"]:
        parts.append(f"{message.role}: {message.content}")
    return "\n\n".join(parts)
```

**Why `recent_ids = {id(m) for m in recent}` uses Python's `id()` rather than comparing message content or an index**: `ConversationMessage` is a frozen dataclass without a unique identifier field of its own (no database ID exists at this layer — that belongs to Chapter 19's model) — `id()` (Python's built-in object identity) is a safe, simple way to determine "which exact message objects were selected into the recent window" without needing to add an artificial identifier field purely for this internal bookkeeping purpose.

**Why `build_context` is the only function in this module that accepts an optional `client` parameter**: it's the only function that might need to make an LLM call (for summarization) — every other function (`select_recent_window`, `total_tokens`, `needs_summarization`) is pure, deterministic Python with no external dependency at all, and deliberately doesn't accept a client parameter it would never use, keeping each function's signature an honest reflection of what it actually needs.

---

## 11. Code Walkthrough

- **`select_recent_window`'s `if cost > budget and kept:` condition is the exact mechanism behind the "always keep at least one message" guarantee**: on the very first iteration, `kept` is still empty, so the condition is `False` regardless of `cost`, and the message is always appended — only on the *second and later* iterations does exceeding the budget actually stop the loop. This one line is worth tracing through carefully, since it's a compact but easy-to-get-subtly-wrong piece of logic.
- **`build_context`'s early return when summarization isn't needed makes the "cheap path" the literal first thing the function checks**: this mirrors a pattern now used consistently across the whole `ai/` package — check whether the expensive branch is actually necessary before doing any of the expensive work, rather than always paying the cost and discarding it if unneeded.
- **This chapter builds zero Django code, on purpose, matching Chapter 11's scope exactly** — worth noticing as a deliberate rhythm in how Volume 4 and Volume 5 are structured: heavy Django-integration chapters (12, 17) alternate with focused, pure-`ai/` chapters (11, 18) that keep each concern cleanly separated rather than always mixing Django and AI-layer work together.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `select_recent_window` returns messages out of order | Forgetting the final `kept.reverse()` after building the list newest-first | Confirm the reverse call is present — the function must always return chronological order, since that's what a prompt needs |
| Summarization triggers on every single call for a moderately-long conversation | `trigger_tokens` set too close to `recency_window_tokens` | Keep a meaningful gap between the two constants (the Chapter 18 defaults: 1500 vs 3000) — a small gap defeats the purpose described in Theory §2.3 |
| `build_context` returns an empty `recent_messages` list for a genuinely empty conversation | This is actually correct behavior, not a bug | Chapter 19's chat view should handle the "no messages yet" case explicitly rather than assuming `build_context` never returns an empty list |
| Real provider token/context-limit errors despite this module's estimates looking fine | The character-based heuristic diverged meaningfully from the model's real tokenizer for this specific content (e.g., heavy non-English text or code) | This is the documented limitation from Section 3 — the fix is swapping `estimate_tokens`'s implementation for a real tokenizer, isolated to that one function |

---

## 13. Debugging

```bash
# 1. Exercise the whole pipeline with fake messages, no LLM involved for the short-conversation path
docker compose exec web python manage.py shell -c "
from ai.memory.message import ConversationMessage
from ai.memory.conversation_memory import build_context, format_context_for_prompt

messages = [
    ConversationMessage(role='user', content='I want to visit Japan in June.'),
    ConversationMessage(role='assistant', content='Great choice! Any budget in mind?'),
    ConversationMessage(role='user', content='Moderate, around \$150/day.'),
]
context = build_context(messages)
print(context['summary'])
print(format_context_for_prompt(context))
"

# 2. Confirm token estimation behaves sensibly
docker compose exec web python manage.py shell -c "
from ai.memory.token_estimator import estimate_tokens
print(estimate_tokens('a short message'))
print(estimate_tokens('a' * 4000))
"
```

**Rollback strategy:** since this module has no persistent state of its own, there's nothing to roll back — any mistake is fixed purely by editing the function and re-running tests, the same cheapest-possible debugging loop as every other pure-`ai/` chapter.

---

## 14. Testing

### 14.1 `ai/tests/test_token_estimator.py`

```python
from ai.memory.message import ConversationMessage
from ai.memory.token_estimator import estimate_message_tokens, estimate_tokens


def test_estimate_tokens_roughly_matches_char_count_heuristic():
    assert estimate_tokens("a" * 400) == 100


def test_estimate_tokens_never_returns_zero():
    assert estimate_tokens("") == 1
    assert estimate_tokens("hi") >= 1


def test_estimate_message_tokens_includes_overhead():
    message = ConversationMessage(role="user", content="a" * 100)
    assert estimate_message_tokens(message) == estimate_tokens("a" * 100) + 4
```

### 14.2 `ai/tests/test_conversation_memory.py`

```python
from unittest.mock import MagicMock

from ai.memory.conversation_memory import (
    build_context,
    format_context_for_prompt,
    needs_summarization,
    select_recent_window,
    total_tokens,
)
from ai.memory.message import ConversationMessage


def _messages(n: int, content_len: int = 20) -> list[ConversationMessage]:
    return [
        ConversationMessage(role="user" if i % 2 == 0 else "assistant", content="x" * content_len)
        for i in range(n)
    ]


class TestSelectRecentWindow:
    def test_returns_all_messages_when_well_under_budget(self):
        messages = _messages(3, content_len=10)
        result = select_recent_window(messages, max_tokens=1000)
        assert result == messages

    def test_always_keeps_at_least_the_most_recent_message(self):
        oversized = [ConversationMessage(role="user", content="x" * 10_000)]
        result = select_recent_window(oversized, max_tokens=10)
        assert len(result) == 1

    def test_preserves_chronological_order(self):
        messages = _messages(5, content_len=10)
        result = select_recent_window(messages, max_tokens=1000)
        assert [m.content for m in result] == [m.content for m in messages]

    def test_trims_oldest_messages_first_when_over_budget(self):
        messages = _messages(10, content_len=100)  # each ~29 tokens with overhead
        result = select_recent_window(messages, max_tokens=100)
        assert len(result) < len(messages)
        # the LAST message in the original list must be present (most recent)
        assert result[-1] == messages[-1]


class TestNeedsSummarization:
    def test_short_conversation_does_not_need_summarization(self):
        messages = _messages(3, content_len=20)
        assert needs_summarization(messages) is False

    def test_long_conversation_needs_summarization(self):
        messages = _messages(50, content_len=500)
        assert needs_summarization(messages) is True


class TestBuildContext:
    def test_short_conversation_skips_summarization_entirely(self):
        messages = _messages(3, content_len=20)
        fake_client = MagicMock()

        context = build_context(messages, client=fake_client)

        assert context["summary"] is None
        assert len(context["recent_messages"]) == 3
        fake_client.call.assert_not_called()

    def test_long_conversation_triggers_summarization(self):
        messages = _messages(50, content_len=500)
        fake_client = MagicMock()
        fake_client.call.return_value = "The traveler wants to visit Japan in June with a moderate budget."

        context = build_context(messages, client=fake_client)

        assert context["summary"] == "The traveler wants to visit Japan in June with a moderate budget."
        assert len(context["recent_messages"]) < len(messages)
        fake_client.call.assert_called_once()

    def test_summarized_and_recent_messages_do_not_overlap(self):
        messages = _messages(50, content_len=500)
        fake_client = MagicMock()
        fake_client.call.return_value = "summary text"

        context = build_context(messages, client=fake_client)
        recent_contents = {m.content for m in context["recent_messages"]}
        call_kwargs = fake_client.call.call_args.kwargs
        for content in recent_contents:
            assert content not in call_kwargs["user_prompt"] or list(recent_contents).count(content) < len(messages)


class TestFormatContextForPrompt:
    def test_formats_summary_and_messages_together(self):
        context = {
            "summary": "Earlier: discussed Japan trip.",
            "recent_messages": [ConversationMessage(role="user", content="What about food?")],
        }
        formatted = format_context_for_prompt(context)
        assert "Earlier: discussed Japan trip." in formatted
        assert "user: What about food?" in formatted

    def test_formats_without_summary_when_none(self):
        context = {"summary": None, "recent_messages": [ConversationMessage(role="user", content="Hi")]}
        formatted = format_context_for_prompt(context)
        assert "[Earlier conversation summary]" not in formatted
        assert "user: Hi" in formatted
```

Run everything:

```bash
docker compose exec web pytest ai/tests/test_token_estimator.py ai/tests/test_conversation_memory.py -v
```

---

## 15. Git Commit

```bash
git add ai/memory/ ai/prompts/memory_summarizer_v1.py ai/tests/test_token_estimator.py ai/tests/test_conversation_memory.py
git commit -m "feat(ai): memory & conversation state — pure transformation layer

- ConversationMessage: plain frozen dataclass, not Pydantic — no
  validation need for our own already-known-good data (contrast
  with ai/agents/schemas.py, which validates untrusted LLM output)
- token_estimator.py: deliberate character-count heuristic, NOT a
  real tokenizer — documented limitation, isolated to one function
  if real precision is ever needed (same YAGNI stance as Chapter 6/14)
- select_recent_window: newest-first walk, ALWAYS keeps at least the
  most recent message even if it alone exceeds budget; returns
  chronological order
- needs_summarization has its own, meaningfully higher threshold than
  the recency window budget — prevents an extra LLM call on nearly
  every turn of a moderately-long conversation
- build_context: short-circuits to zero LLM calls when history
  already fits; summary recomputed fresh each time (no incremental/
  cached summary in this version — documented as a deliberate v1
  simplification, unlike Chapter 15's accept/reject preservation,
  because summaries have no user decision to protect)
- Zero Django code touched this chapter — persistence is explicitly
  Chapter 19's responsibility; this module only transforms whatever
  messages it's handed

Chapter 18 of Implementation Bible — Volume 5 begins."
```

---

## 16. Checklist

- [ ] `ConversationMessage` is a plain dataclass, not Pydantic — reasoning documented
- [ ] `estimate_tokens` is explicitly labeled approximate; its limitation and fix path are documented, not hidden
- [ ] `select_recent_window` always returns at least one message and preserves chronological order — both proven by dedicated tests
- [ ] `needs_summarization`'s trigger threshold is meaningfully higher than the recency window budget
- [ ] `build_context` makes zero LLM calls for a short conversation — verified via `assert_not_called()`
- [ ] `build_context` makes exactly one LLM call for a long conversation — verified via `assert_called_once()`
- [ ] This chapter introduces zero new Django files, zero migrations — confirmed scope match with Chapter 11
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 19 — `chat` App** is where this chapter's pure transformation layer finally gets a real caller: a genuine Django app with `ChatSession` and `ChatMessage` models, persisting real conversation history, converting stored `ChatMessage` rows into `ConversationMessage` objects, calling `build_context()` from this chapter, and routing the result through `ai_agents` (never `ai/` directly — the single-door rule from Chapter 12 applies here too) to get a conversational reply. This is also where the project's chat-to-agent bridge pattern gets built for the first time. Say **"Continue to Chapter 19"** when ready.
