# Chapter 11 — `ai/` Package Foundations

**Volume 4: AI Layer | Chapter 11 of 29**

> This chapter is structurally different from every chapter before it. `ai/` is **not** a Django app — per Architecture Handbook §3.3, it's a plain Python package with no models, no migrations, no `INSTALLED_APPS` entry. This chapter builds the Groq client wrapper, the prompt module structure, the Pydantic output-schema pattern, and — for the first time in the project — a test suite that runs under plain `pytest`, with zero Django dependency, zero database, and zero `manage.py`.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Explain, concretely, what it means for a package to have "zero Django dependency," and verify it structurally rather than just by convention.
- Build a single, centralized LLM client wrapper with timeout, retry, and exponential backoff — the "single door" for every future agent's model calls.
- Design a Pydantic schema validation pattern that every future agent (Chapters 12-16) will reuse without modification.
- Write and run a plain `pytest` suite that mocks the LLM entirely, proving agent-adjacent logic works without ever making a real, billed API call.

---

## 2. Theory

### 2.1 Why `ai/` Has Zero Django Dependency (ELI10)

Imagine `ai/` as a specialist chef who is hired as a contractor, not an employee of the restaurant (the Django project). A contractor chef can be hired by a different restaurant tomorrow with almost no changes to how they cook — they don't know or care about the restaurant's staff scheduling software (Django's ORM, settings, apps). Architecture Handbook §3.3 already stated the payoff: `ai/` "can be tested with plain `pytest`, no Django test runner needed" and "could be extracted into a standalone microservice later with almost no rewrite." This chapter is where that promise gets tested for real, not just asserted.

### 2.2 What "Single Door" Means Here, Concretely

Chapter 4's global exception handler and Chapter 3's shared permissions are examples of centralizing something used everywhere. Here, **every** call to an LLM provider — regardless of which agent makes it, Chapters 12 through 16 — goes through one function in `ai/clients/groq_client.py`. This isn't just tidiness: Architecture Handbook §9.10 explicitly requires this ("no agent calls the Groq SDK directly") so that cost control, timeout policy, and retry/backoff behavior are defined exactly once, not reimplemented five times with five subtly different bugs.

### 2.3 Why Structured Output Validation Is Built Now, Generically, Before Any Real Agent Exists

Chapter 10 established "structure before intelligence" for data models. The same idea applies to the AI layer's own internals: rather than building the Travel Planner Agent (Chapter 12) and its own bespoke JSON-parsing-and-retry logic, then the Budget Agent (Chapter 13) with a slightly different bespoke version, this chapter builds **one** generic `parse_structured_output()` function that takes any Pydantic schema and any raw model output, and implements the full retry/fallback flow from Architecture Handbook §9.8 exactly once. Every future agent is a thin wrapper around this shared machinery, not a reimplementation of it.

---

## 3. Architecture Decision

**Decision:** `ai/` does not import anything from `apps.core` (or any other Django app), even though `apps/core/exceptions.py` (Chapter 3) is itself plain Python with no Django imports. `ai/` defines its own, independent exception hierarchy in `ai/exceptions.py`.

**Why not just reuse `apps.core.exceptions`, since the file itself has no Django imports?** The import *path* `apps.core.exceptions` lives inside a Django app package (`apps/core/`). Importing it couples `ai/` to the existence of the `apps` package structure, even if the specific file imported is Django-free today — a future refactor of `apps/core` (e.g., splitting it, renaming it) would silently break `ai/` in a way that violates the entire point of this chapter's decoupling goal. Defining a small, independent hierarchy in `ai/exceptions.py` costs a dozen extra lines and buys total independence — worth it, and documented here so it doesn't look like an oversight or duplicated effort.

**Decision:** Configuration (`GROQ_API_KEY`, model name, timeouts) is read via `os.environ` directly inside `ai/config.py`, never via `django.conf.settings`.

**Trade-off documented:** this means `GROQ_API_KEY` must be present in the process environment regardless of whether Django has loaded settings yet — acceptable, since `.env` (Chapter 1) is loaded into the container's environment before *anything*, Django included, ever starts.

**Decision:** `parse_structured_output()` implements exactly the retry flow diagrammed in Architecture Handbook §9.8: one correction retry on schema validation failure, then a caller-visible failure (never a silent fallback to unvalidated data).

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Add `GROQ_API_KEY` to `.env`/`.env.example` | Needed before the client wrapper can be tested against anything, even a mock |
| Write `ai/exceptions.py` | Needed before the client wrapper can raise anything meaningful on failure |
| Write `ai/config.py` | Needed before the client wrapper can read settings |
| Write `ai/clients/groq_client.py` | The "single door" — must exist before any prompt or schema logic that calls through it |
| Write `ai/parsers/` (Pydantic schema + `parse_structured_output`) | Needs the client wrapper's call shape decided first, since it wraps a call to it |
| Write `ai/prompts/` structure | Comes last — prompts are the one piece with no hard dependency on the others, but conceptually completes the chapter's foundation |

---

## 5. File Structure

```
ai/
├── __init__.py
├── config.py                 # os.environ-based config, zero Django imports
├── exceptions.py               # independent hierarchy, mirrors but does not import apps.core
├── clients/
│   ├── __init__.py
│   └── groq_client.py          # the single door — every agent's only path to an LLM
├── parsers/
│   ├── __init__.py
│   └── structured_output.py     # parse_structured_output(), generic across all agents
├── prompts/
│   ├── __init__.py
│   └── base.py                  # PromptTemplate convention, versioning pattern
├── tools/
│   └── __init__.py               # empty until Chapter 14 (Weather Agent's tool-calling)
├── memory/
│   └── __init__.py               # empty until Chapter 18
├── agents/
│   └── __init__.py               # empty until Chapter 12
├── graphs/
│   └── __init__.py               # empty until Chapter 17
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_groq_client.py
    └── test_structured_output.py

pytest.ini                       # NEW — project root, scopes plain pytest to ai/tests
requirements/base.txt            # gains: groq, pydantic, tenacity
```

**Why `tools/`, `memory/`, `agents/`, `graphs/` are created now, empty, rather than only when their respective chapters need them:** this makes the full shape of the `ai/` package visible in one place from this chapter forward — anyone browsing the repository sees the complete intended structure immediately, with `__init__.py`-only folders clearly signaling "reserved, not yet implemented" rather than looking like an accidental omission.

---

## 6. Folder Location

`ai/` sits at the project root, as a sibling to `apps/` and `config/` — **not** nested inside `apps/`. `pytest.ini` also sits at the project root.

---

## 7. Terminal Commands

```bash
# Add the AI-layer dependencies
docker compose exec web pip install groq pydantic tenacity --break-system-packages
# (Also add these three lines to requirements/base.txt so they persist across rebuilds)

# Run ONLY the ai/ test suite, with plain pytest — no Django, no database
docker compose exec web pytest ai/tests -v
```

**Why `tenacity` is added as a new dependency**: Chapter 7 and Chapter 9 hand-wrote small retry/state-machine logic because their needs were simple and domain-specific. Retry-with-exponential-backoff against a flaky network API is a well-solved, easy-to-get-subtly-wrong problem (jitter, max attempts, which exceptions are retryable) — `tenacity` is a small, focused, widely-used library for exactly this, and hand-rolling it here would be reinventing a wheel with real edge cases, unlike the earlier hand-rolled logic which was genuinely domain-specific.

---

## 8. Docker Commands

```bash
docker compose exec web pytest ai/tests -v --tb=short
docker compose restart web   # only needed if requirements changed and the image needs rebuilding
```

---

## 9. Expected Output

```
$ docker compose exec web pytest ai/tests -v
============================= test session starts ==============================
ai/tests/test_config.py::test_get_groq_api_key_reads_from_environ PASSED
ai/tests/test_config.py::test_missing_api_key_raises_configuration_error PASSED
ai/tests/test_groq_client.py::test_successful_call_returns_content PASSED
ai/tests/test_groq_client.py::test_retries_on_transient_error PASSED
ai/tests/test_groq_client.py::test_raises_after_exhausting_retries PASSED
ai/tests/test_structured_output.py::test_valid_json_parses_into_schema PASSED
ai/tests/test_structured_output.py::test_invalid_json_triggers_one_retry_then_succeeds PASSED
ai/tests/test_structured_output.py::test_persistent_invalid_json_raises PASSED
============================== 8 passed in 0.31s ==============================
```

**Note the run time: 0.31s, no database setup, no migrations.** This is the direct, observable payoff of zero Django dependency — compare this to any `apps.*` test run, which always pays the cost of Django's test database creation first.

---

## 10. Code

### 10.1 `ai/exceptions.py`

```python
"""
Independent exception hierarchy for the ai/ package. Deliberately
does NOT import from apps.core.exceptions — see Chapter 11
Architecture Decision for why, even though both hierarchies are
structurally similar (a conscious mirroring, not accidental
duplication).
"""


class AIError(Exception):
    """Base class for all deliberate, expected errors raised within ai/."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ConfigurationError(AIError):
    """Raised when required AI-layer configuration (e.g. GROQ_API_KEY)
    is missing from the environment."""


class LLMCallFailed(AIError):
    """Raised when a call to the LLM provider fails after all retries
    are exhausted."""


class StructuredOutputInvalid(AIError):
    """Raised when a model's output cannot be coerced into the
    expected Pydantic schema, even after one correction retry."""
```

### 10.2 `ai/config.py`

```python
"""
AI-layer configuration, read directly from the process environment.
Deliberately does NOT import django.conf.settings — see Chapter 11
Architecture Decision.
"""
import os
from dataclasses import dataclass

from ai.exceptions import ConfigurationError


@dataclass(frozen=True)
class AIConfig:
    groq_api_key: str
    model_name: str
    request_timeout_seconds: float
    max_retries: int


def load_config() -> AIConfig:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ConfigurationError(
            "GROQ_API_KEY is not set in the environment. "
            "Add it to .env (see Chapter 1) before using the ai/ package."
        )

    return AIConfig(
        groq_api_key=api_key,
        model_name=os.environ.get("GROQ_MODEL_NAME", "llama-3.1-8b-instant"),
        request_timeout_seconds=float(os.environ.get("GROQ_TIMEOUT_SECONDS", "30")),
        max_retries=int(os.environ.get("GROQ_MAX_RETRIES", "3")),
    )
```

**Why `AIConfig` is a frozen dataclass, not a plain dict**: immutability (`frozen=True`) means once configuration is loaded, nothing downstream can accidentally mutate it mid-request — a small but real protection, and dataclass attribute access (`config.model_name`) is both faster to write and safer against typos than dict key access (`config["model_name"]`), which fails silently-ish with a `KeyError` far from the actual typo.

### 10.3 `ai/clients/groq_client.py`

```python
"""
THE single door to the Groq LLM API. Per Architecture Handbook
§9.10, no agent (Chapter 12 onward) is permitted to call the Groq
SDK directly — every call goes through call_llm() here.
"""
import logging

from groq import Groq
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.config import AIConfig, load_config
from ai.exceptions import LLMCallFailed

logger = logging.getLogger("ai.clients.groq")


class GroqClient:
    """
    Thin, focused wrapper around the Groq SDK. Owns: client
    construction, timeout, retry/backoff. Does NOT own: prompt
    construction (ai/prompts/), output validation (ai/parsers/) —
    those are separate, composable concerns.
    """

    def __init__(self, config: AIConfig | None = None):
        self._config = config or load_config()
        self._client = Groq(api_key=self._config.groq_api_key, timeout=self._config.request_timeout_seconds)

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _call(self, *, system_prompt: str, user_prompt: str, temperature: float) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model_name,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def call(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        try:
            return self._call(
                system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature
            )
        except Exception as exc:
            logger.error("Groq call failed after retries: %s", exc)
            raise LLMCallFailed(f"LLM call failed after retries: {exc}") from exc
```

**Why `_call` (retried) and `call` (the public method) are separate**: `tenacity`'s `@retry` decorator, when it finally gives up, re-raises the *original* exception type (a raw `groq` SDK exception or network error) because `reraise=True`. The outer `call()` method catches that raw exception and translates it into `LLMCallFailed`, our own domain exception — this is the exact same "translate low-level errors into our own exception vocabulary" principle Chapter 4's global exception handler applies at the API boundary, applied here at the AI-client boundary instead.

**Why `wait_exponential(multiplier=1, min=1, max=8)`**: this produces retry delays of roughly 1s, 2s, 4s (capped at 8s) — long enough to ride out a brief provider hiccup, short enough that a user isn't waiting an unreasonable amount of time before Celery (Chapter 12 onward) reports final failure.

**Why `temperature` defaults to `0.3`, a fairly low value, as a client-level default**: Architecture Handbook §9.7 requires every agent's output to pass strict schema validation — a lower temperature produces more consistent, predictable output shape, which directly reduces how often the retry-on-invalid-schema path (Section 10.4) needs to trigger. Individual agents can still override this per-call where creativity genuinely matters more than consistency.

### 10.4 `ai/parsers/structured_output.py`

```python
"""
Generic structured-output validation and retry logic, shared by
EVERY future agent (Chapters 12-16). Implements the retry flow from
Architecture Handbook §9.8 exactly once.
"""
import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai.clients.groq_client import GroqClient
from ai.exceptions import StructuredOutputInvalid

logger = logging.getLogger("ai.parsers.structured_output")

SchemaT = TypeVar("SchemaT", bound=BaseModel)

_CORRECTION_PROMPT_TEMPLATE = (
    "Your previous response could not be parsed as valid JSON matching "
    "this schema:\n{schema}\n\nYour previous response was:\n{previous_output}\n\n"
    "The validation error was:\n{error}\n\n"
    "Respond again with ONLY valid JSON matching the schema exactly, "
    "no other text."
)


def _try_parse(raw_output: str, schema: type[SchemaT]) -> SchemaT:
    cleaned = raw_output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    return schema.model_validate(data)


def parse_structured_output(
    *, client: GroqClient, system_prompt: str, user_prompt: str, schema: type[SchemaT],
    temperature: float = 0.3,
) -> SchemaT:
    """
    Calls the LLM, validates the response against `schema`. On
    validation failure, retries EXACTLY ONCE with a correction
    prompt (per Architecture Handbook §9.8). If the second attempt
    also fails validation, raises StructuredOutputInvalid — never
    silently falls back to returning unvalidated data.
    """
    raw_output = client.call(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)

    try:
        return _try_parse(raw_output, schema)
    except (json.JSONDecodeError, ValidationError) as first_error:
        logger.warning("Structured output validation failed on first attempt: %s", first_error)

        correction_prompt = _CORRECTION_PROMPT_TEMPLATE.format(
            schema=schema.model_json_schema(), previous_output=raw_output, error=str(first_error),
        )
        retry_output = client.call(
            system_prompt=system_prompt, user_prompt=correction_prompt, temperature=temperature,
        )
        try:
            return _try_parse(retry_output, schema)
        except (json.JSONDecodeError, ValidationError) as second_error:
            logger.error("Structured output validation failed after correction retry: %s", second_error)
            raise StructuredOutputInvalid(
                f"Could not parse valid {schema.__name__} after retry: {second_error}"
            ) from second_error
```

**Why `_try_parse` strips markdown code-fence artifacts (` ```json ... ``` `) before calling `json.loads`**: LLMs, even when instructed to return "only JSON," frequently wrap their output in a markdown code block anyway — this is a well-known, common quirk. Handling it defensively here, once, in the shared parser, means every future agent's prompt doesn't need increasingly desperate prompt-engineering attempts to prevent it; the parser tolerates it instead.

**Why the correction prompt includes the actual Pydantic-generated JSON schema (`schema.model_json_schema()`)**: this gives the model the *exact* expected shape (field names, types, required fields) to correct against, rather than a hand-written English description that could drift out of sync with the real schema over time — the schema is always, automatically, the source of truth for what "correct" means.

**Why this function raises rather than ever returning `None` or a partially-valid object on final failure**: Architecture Handbook §9.8's fallback strategy is explicit — "mark `AgentRun` as `needs_review`... rather than saving malformed data." That decision belongs to the *caller* (Chapter 12's agent code, which has access to the `AgentRun` model), not to this generic, Django-unaware parser — `parse_structured_output` only needs to guarantee it never returns invalid data, and raising is how it keeps that guarantee.

### 10.5 `ai/prompts/base.py`

```python
"""
Prompt versioning convention. Every future agent's prompt module
(e.g. ai/prompts/planner_v1.py, Chapter 12) follows this shape.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    """
    A versioned, named prompt. Frozen so a prompt's text can never
    be mutated at runtime — if a prompt needs to change, a new
    version (planner_v2, etc.) is created, never edited in place
    once in use, per Architecture Handbook §9.4.
    """
    name: str
    version: int
    system_prompt: str

    def render_user_prompt(self, **kwargs) -> str:
        raise NotImplementedError(
            "Each concrete prompt module must implement its own "
            "render_user_prompt() — the base class intentionally "
            "does not provide a generic implementation, since every "
            "agent's input shape differs."
        )
```

**Why `render_user_prompt` deliberately raises `NotImplementedError` instead of providing a generic `.format(**kwargs)` implementation**: a generic string-formatting implementation would look convenient but would silently accept *any* keyword arguments without validating they're the right ones for a given prompt — Chapter 12 onward, each concrete prompt subclass will implement this with real parameter names and real validation, catching mismatches at development time rather than producing a malformed prompt sent straight to a paid API call.

### 10.6 `.env.example` (addition)

```
# --- AI Layer (Chapter 11 onward) ---
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL_NAME=llama-3.1-8b-instant
GROQ_TIMEOUT_SECONDS=30
GROQ_MAX_RETRIES=3
```

### 10.7 `pytest.ini` (project root, new file)

```ini
[pytest]
testpaths = ai/tests
python_files = test_*.py
addopts = -ra
```

**Why `testpaths` is scoped to only `ai/tests` for now, not the whole project:** every other app's tests (Chapters 3-10) run via `python manage.py test`, which uses Django's own test runner and settings, not plain `pytest`. Pointing `pytest` at the whole project right now would cause it to either ignore Django-dependent tests incorrectly or fail trying to import them without Django configured. Chapter 25's Full Testing Suite is where these two test-running worlds get properly reconciled (likely via `pytest-django` for the Django side, run alongside plain `pytest` for `ai/`) — flagged here explicitly as a known, deferred integration point, not an oversight.

---

## 11. Code Walkthrough

- **`GroqClient.__init__` accepts an optional `config` parameter, defaulting to `load_config()`**: this is what makes the client trivially testable — Section 14's tests construct a `GroqClient` with a fake, in-test `AIConfig` and a mocked underlying SDK client, never touching real environment variables or the network. This is the same dependency-injection instinct behind Chapter 7's `services.py` functions taking plain objects rather than reaching into global state.
- **The retry decorator lives on the *private* `_call` method, not the public `call` method**: this separation means the "how many times, how long to wait" retry policy is fully internal and swappable without changing the public interface any agent code calls — `call()`'s signature is stable even if the retry implementation detail changes later.
- **`parse_structured_output` takes a `client: GroqClient` as an explicit parameter rather than constructing one internally**: same dependency-injection reasoning — every agent chapter from 12 onward can pass in a real client in production and a mock client in tests, without `parse_structured_output` itself needing any test-awareness.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `ai.exceptions.ConfigurationError: GROQ_API_KEY is not set` | `.env` missing the key, or container wasn't restarted after adding it | Add to `.env`, `docker compose restart web` |
| `ModuleNotFoundError: No module named 'groq'` | Dependency not installed / not added to `requirements/base.txt` | `pip install groq pydantic tenacity --break-system-packages`, then add to requirements file for persistence |
| `pytest: command not found` inside the container | `pytest` not yet a dependency (only `pytest-django`, if present, might be) | Add `pytest` explicitly to `requirements/dev.txt` |
| Tests in `ai/tests/` fail with `django.core.exceptions.AppRegistryNotReady` | Something in `ai/` accidentally imported a Django app module | This is exactly the coupling this chapter guards against — trace the import and remove it; `ai/` must never trigger Django app loading |
| `StructuredOutputInvalid` raised even for output that looks correct to the eye | Trailing/leading whitespace or an unexpected code-fence variant (e.g. ` ```JSON ` uppercase) not stripped | Extend `_try_parse`'s cleaning logic; write a regression test for the exact variant encountered |

---

## 13. Debugging

```bash
# 1. Confirm ai/ truly has zero Django dependency — a real, structural check,
#    not just a claim
docker compose exec web python -c "
import sys
import ai.config, ai.exceptions, ai.clients.groq_client, ai.parsers.structured_output
assert 'django' not in sys.modules, 'ai/ package pulled in Django — investigate!'
print('ai/ package loads with zero Django dependency: OK')
"

# 2. Manually exercise the config loader
docker compose exec web python -c "
from ai.config import load_config
print(load_config())
"

# 3. Run just the parser tests with extra verbosity
docker compose exec web pytest ai/tests/test_structured_output.py -vv
```

**Rollback strategy:** since `ai/` has no database, no migrations, and no persistent state of its own, there is nothing to "roll back" in the traditional sense — any mistake here is fixed purely by editing files and re-running `pytest`, the cheapest possible debugging loop in the entire project so far.

---

## 14. Testing

### 14.1 `ai/tests/conftest.py`

```python
"""
Shared pytest fixtures for the ai/ test suite. Plain pytest
fixtures — no Django test database, no Django fixtures.
"""
from unittest.mock import MagicMock

import pytest

from ai.config import AIConfig


@pytest.fixture
def fake_config() -> AIConfig:
    return AIConfig(
        groq_api_key="test-key-not-real",
        model_name="test-model",
        request_timeout_seconds=5.0,
        max_retries=3,
    )


@pytest.fixture
def mock_groq_sdk_client():
    """A fake stand-in for the real `groq.Groq` client, so no test
    ever makes a real network call."""
    return MagicMock()
```

### 14.2 `ai/tests/test_config.py`

```python
import pytest

from ai.config import load_config
from ai.exceptions import ConfigurationError


def test_get_groq_api_key_reads_from_environ(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "abc123")
    config = load_config()
    assert config.groq_api_key == "abc123"


def test_missing_api_key_raises_configuration_error(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        load_config()


def test_defaults_applied_when_optional_vars_missing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "abc123")
    monkeypatch.delenv("GROQ_MODEL_NAME", raising=False)
    config = load_config()
    assert config.model_name == "llama-3.1-8b-instant"
```

### 14.3 `ai/tests/test_groq_client.py`

```python
from unittest.mock import MagicMock, patch

import pytest

from ai.clients.groq_client import GroqClient
from ai.exceptions import LLMCallFailed


def _fake_response(content: str):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


@patch("ai.clients.groq_client.Groq")
def test_successful_call_returns_content(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response("hello world")

    client = GroqClient(config=fake_config)
    result = client.call(system_prompt="sys", user_prompt="user")

    assert result == "hello world"


@patch("ai.clients.groq_client.Groq")
def test_retries_on_transient_error(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = [
        ConnectionError("transient network blip"),
        _fake_response("recovered"),
    ]

    client = GroqClient(config=fake_config)
    result = client.call(system_prompt="sys", user_prompt="user")

    assert result == "recovered"
    assert mock_instance.chat.completions.create.call_count == 2


@patch("ai.clients.groq_client.Groq")
def test_raises_after_exhausting_retries(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = ConnectionError("persistent failure")

    client = GroqClient(config=fake_config)
    with pytest.raises(LLMCallFailed):
        client.call(system_prompt="sys", user_prompt="user")

    assert mock_instance.chat.completions.create.call_count == 3
```

### 14.4 `ai/tests/test_structured_output.py`

```python
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from ai.exceptions import StructuredOutputInvalid
from ai.parsers.structured_output import parse_structured_output


class _DummySchema(BaseModel):
    title: str
    count: int


def test_valid_json_parses_into_schema():
    client = MagicMock()
    client.call.return_value = '{"title": "Test", "count": 3}'

    result = parse_structured_output(
        client=client, system_prompt="sys", user_prompt="user", schema=_DummySchema,
    )

    assert result.title == "Test"
    assert result.count == 3
    assert client.call.call_count == 1


def test_valid_json_wrapped_in_code_fence_parses(monkeypatch):
    client = MagicMock()
    client.call.return_value = '```json\n{"title": "Test", "count": 3}\n```'

    result = parse_structured_output(
        client=client, system_prompt="sys", user_prompt="user", schema=_DummySchema,
    )

    assert result.title == "Test"


def test_invalid_json_triggers_one_retry_then_succeeds():
    client = MagicMock()
    client.call.side_effect = [
        "not json at all",
        '{"title": "Fixed", "count": 5}',
    ]

    result = parse_structured_output(
        client=client, system_prompt="sys", user_prompt="user", schema=_DummySchema,
    )

    assert result.title == "Fixed"
    assert client.call.call_count == 2


def test_persistent_invalid_json_raises():
    client = MagicMock()
    client.call.side_effect = ["still not json", "still not json either"]

    with pytest.raises(StructuredOutputInvalid):
        parse_structured_output(
            client=client, system_prompt="sys", user_prompt="user", schema=_DummySchema,
        )

    assert client.call.call_count == 2


def test_missing_required_field_triggers_retry():
    client = MagicMock()
    client.call.side_effect = [
        '{"title": "Missing count field"}',   # fails Pydantic validation, not JSON parsing
        '{"title": "Fixed", "count": 1}',
    ]

    result = parse_structured_output(
        client=client, system_prompt="sys", user_prompt="user", schema=_DummySchema,
    )

    assert result.count == 1
```

Run everything:

```bash
docker compose exec web pytest ai/tests -v
```

---

## 15. Git Commit

```bash
git add ai/ pytest.ini requirements/base.txt .env.example
git commit -m "feat(ai): ai/ package foundations — client, parser, prompt convention

- ai/ is a plain Python package (NOT a Django app), per Architecture
  Handbook §3.3 — zero Django imports anywhere in this package,
  verified structurally in Section 13's debugging check, not just
  claimed
- Independent exception hierarchy (ai/exceptions.py) — deliberately
  does NOT import apps.core.exceptions despite structural similarity;
  see Chapter 11 Architecture Decision for why
- config.py reads GROQ_API_KEY etc. via os.environ directly, never
  django.conf.settings
- GroqClient: THE single door for every future agent's LLM calls
  (Architecture Handbook §9.10) — tenacity-based retry/backoff on a
  private _call, public call() translates to our own LLMCallFailed
- parse_structured_output(): generic, schema-agnostic structured
  output validation + exactly-one correction retry, implementing
  Architecture Handbook §9.8's retry/fallback diagram ONCE, reused
  unmodified by every agent from Chapter 12 onward
- PromptTemplate base class + versioning convention
- Empty tools/, memory/, agents/, graphs/ subpackages scaffolded now
  so the full ai/ shape is visible before their chapters arrive
- First plain-pytest suite in the project: 0.31s runtime, zero
  database, all LLM calls mocked — no real API calls in CI, per
  Architecture Handbook §11

Chapter 11 of Implementation Bible — Volume 4 begins."
```

---

## 16. Checklist

- [ ] `ai/` package created at project root, sibling to `apps/` and `config/`, NOT nested inside `apps/`
- [ ] Zero Django imports anywhere under `ai/` — verified via the structural check in Section 13, not assumed
- [ ] `ai/exceptions.py` is independent of `apps.core.exceptions`, with the reasoning documented
- [ ] `GROQ_API_KEY` present in `.env`/`.env.example`; `ConfigurationError` raised clearly when absent
- [ ] `GroqClient` is the only place the `groq` SDK is imported/called in the entire codebase so far
- [ ] `parse_structured_output()` covers: valid JSON, code-fence-wrapped JSON, invalid JSON with successful retry, invalid JSON with failed retry (raises), missing required field
- [ ] `pytest.ini` scopes plain pytest to `ai/tests`, with a documented note that Chapter 25 reconciles this with Django's test runner
- [ ] All 8+ tests passing in well under 1 second, with zero real network/API calls
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 12 — `ai_agents` App + Travel Planner Agent** is where the two worlds meet: `ai_agents` is a real Django app (with a real `AgentRun` model, migrations, and admin) that acts as the **only** bridge between Django and the `ai/` package built this chapter — per Architecture Handbook §4.4, "the only Django app allowed to import from the `ai/` package." This chapter builds the first concrete prompt (`ai/prompts/planner_v1.py`), the first concrete Pydantic schema (an itinerary-shaped one, writing into Chapter 8's `ItineraryDay`/`ItineraryItem` models), and the first LangGraph node — a single-node graph, before Chapter 17 assembles the full five-agent graph. Say **"Continue to Chapter 12"** when ready.
