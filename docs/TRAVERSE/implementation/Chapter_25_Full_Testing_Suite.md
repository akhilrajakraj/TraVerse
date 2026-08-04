# Chapter 25 — Full Testing Suite

**Volume 7: Hardening & Production | Chapter 25 of 29**

> Volume 7 begins. With 24 chapters and roughly two dozen apps' worth of individually-tested code in place, this chapter takes stock rather than building anything new. It consolidates the plain-`pytest` (`ai/`) and Django (`manage.py test`) test-running worlds that Chapter 11 explicitly deferred, introduces a dedicated test settings module, formalizes coverage measurement with a real threshold, and establishes the regression-test discipline Architecture Handbook §11 called for from the very beginning but that no chapter has yet given a concrete home.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Run the entire project's test suite — every `ai/tests/` file and every app's `tests/` package — through a single `pytest` invocation, without rewriting any of the ~20 chapters' worth of `django.test.TestCase`-based tests already written.
- Build a dedicated `config/settings/test.py`, understanding exactly which settings should differ from `dev`/`prod` during test runs and why.
- Configure coverage measurement with a real, enforced threshold, and correctly exclude what shouldn't count toward it (migrations, the tests themselves).
- Establish a durable convention for regression tests — one per previously-fixed bug, named and documented so it's never accidentally deleted during a later refactor.

---

## 2. Theory

### 2.1 Why Two Test-Running Worlds Existed At All (ELI10)

Chapter 11 built `ai/` with a hard rule: zero Django dependency. Testing it with Django's own test runner (`manage.py test`) would have meant giving `ai/`'s tests access to Django's settings and app registry just to run — exactly the coupling Chapter 11 was built to avoid. So `ai/` got plain `pytest`, fast and Django-free, while every other app kept using `manage.py test`. This was the right call *at the time*, but it left two separate commands needed to run "all the tests" — a rough edge Chapter 11 explicitly flagged as deferred, not forgotten.

### 2.2 Why `pytest-django` Doesn't Require Rewriting Any Existing Test

Here's the detail that makes today's chapter cheap rather than a massive rewrite: `django.test.TestCase` is itself a subclass of Python's built-in `unittest.TestCase`, and `pytest` has always been able to discover and run *any* `unittest.TestCase` subclass natively, Django or not. What was actually missing wasn't the ability to *run* Django-style tests under `pytest` — it was Django itself never being *configured* (settings loaded, apps registered) before `pytest` started collecting tests. `pytest-django` solves exactly that one gap: point it at a settings module, and every `TestCase`-based test written since Chapter 3 runs completely unmodified.

### 2.3 Why a Dedicated `config/settings/test.py`, Not Just Reusing `dev.py`

Tests have different needs than local development: password hashing should be fast (not the slow, deliberately-expensive hashers real security requires — Chapter 4's `create_user` calls happen dozens of times per test run), Celery tasks should execute synchronously and immediately rather than requiring a live worker process, and the cache backend should be in-memory rather than depending on a live Redis connection the test environment might not have. `dev.py` was never designed with these needs in mind — a dedicated `test.py`, inheriting from `base.py` like every other settings file, is the correct place for them.

---

## 3. Architecture Decision

**Decision:** `pytest-django` is added, with `DJANGO_SETTINGS_MODULE` pointed at a new `config/settings/test.py`; `pytest.ini`'s `testpaths` is expanded to cover both `ai/tests` and every app's `tests/` package.

**Decision:** `config/settings/test.py` sets `CELERY_TASK_ALWAYS_EAGER = True` (Celery tasks run synchronously, in-process, no live worker needed) and a fast password hasher — both purely for test-run speed and isolation, never used in `dev`/`prod`.

**Decision:** A root-level `conftest.py` sets `GROQ_API_KEY` to an obviously-fake value if it isn't already set, ensuring that any test which accidentally isn't mocking `GroqClient` (a real bug worth catching) fails loudly with an authentication error rather than silently succeeding with a real, billed API call.

**Decision:** Coverage is measured via `pytest-cov`, with a `fail_under = 85` threshold enforced in CI-facing runs, and migrations/tests themselves excluded from the count.

**Trade-off documented:** 85% is a target, not a claim that every line matters equally — some lines (Django admin boilerplate, `__str__` methods) contribute little to real confidence even when covered. The threshold exists to catch *meaningful, accidental* coverage regressions, not to be treated as a number to game with trivial tests.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Write `config/settings/test.py` | Needed before `pytest-django` has anything correct to point at |
| Update `pytest.ini` | Needed before a single consolidated run is possible |
| Add the root `conftest.py` safety net | Needed before running the full suite for the first time, to protect against any accidentally-unmocked test |
| Configure coverage (`.coveragerc`) | Comes after the suite runs cleanly, since coverage measurement needs a working baseline run first |
| Write the regression test convention + example | Last — a discipline for the future, not something retroactively applied to all 24 prior chapters |

---

## 5. File Structure

```
config/settings/
└── test.py                        # NEW

conftest.py                          # NEW — project root, GROQ_API_KEY safety net
pytest.ini                            # MODIFIED — expanded testpaths, DJANGO_SETTINGS_MODULE
.coveragerc                           # NEW

requirements/
└── dev.txt                         # MODIFIED — pytest-django, pytest-cov

apps/trips/tests/
└── test_regressions.py               # NEW — example regression test, establishes the convention

scripts/
└── run_full_test_suite.sh             # NEW — single command, forward-referenced by Chapter 28
```

---

## 6. Folder Location

`config/settings/test.py` alongside `base.py`/`dev.py`/`prod.py`. `conftest.py`, `pytest.ini`, `.coveragerc` at the project root.

---

## 7. Terminal Commands

```bash
docker compose exec web pip install pytest-django pytest-cov --break-system-packages
# add both to requirements/dev.txt

# The ONE command that now runs everything:
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
======================= test session starts ========================
collected 340 items

ai/tests/test_config.py .....                                  [  1%]
ai/tests/test_groq_client.py .....                              [  3%]
...
apps/accounts/tests/test_models.py .....                        [ 22%]
apps/accounts/tests/test_views.py .......                       [ 25%]
...
apps/trips/tests/test_regressions.py .                          [ 91%]
...
apps/analytics/tests/test_views.py ...                          [100%]

---------- coverage: platform linux, python 3.12 -----------
Name                              Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
ai/agents/travel_planner.py          22      1    95%   47
apps/trips/services.py               38      2    95%   61-62
...
-----------------------------------------------------------------
TOTAL                               4180    412    90%

======================= 340 passed in 38.42s ========================
```

**Note the single command, single run, single coverage report — covering both `ai/` and every Django app, something no prior chapter could do in one invocation.**

---

## 10. Code

### 10.1 `config/settings/test.py`

```python
"""
Settings used ONLY during test runs. Inherits from base.py like
dev.py and prod.py — never used for local development or real
deployment. See Chapter 25 Theory §2.3 for why these specific
overrides exist.
"""
from .base import *  # noqa: F401,F403

DEBUG = False  # test prod-like error-handling behavior, not dev-mode tracebacks

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # fast, INSECURE — test-only
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

**Why `DEBUG = False`, when many projects default to `DEBUG = True` for tests to get richer tracebacks**: Chapter 4's global exception handler and several other error-response paths behave differently depending on `DEBUG` — testing with `DEBUG = True` risks a class of "passes in tests, breaks in production" surprise, exactly the opposite of what a test suite should protect against. Rich tracebacks are still available through `pytest`'s own failure output regardless of Django's `DEBUG` setting.

**Why `CELERY_TASK_ALWAYS_EAGER = True`**: without this, every test touching a Celery-dispatched function (Chapter 12's `run_travel_planner_task`, Chapter 22's `send_notification_task`) would need a live Celery worker process running just to execute during tests — impractical and slow. `ALWAYS_EAGER` makes `.delay()` calls execute synchronously, in-process, immediately — the task runs as a normal Python function call, with no live worker or message broker needed at all.

### 10.2 `conftest.py` (project root — new)

```python
"""
Project-wide pytest configuration, loaded automatically before any
test collection. The ONE job here: guarantee GROQ_API_KEY is always
set to an obviously-fake value during test runs, so that any test
which accidentally isn't mocking GroqClient fails LOUDLY with an
authentication error, rather than silently succeeding with a real,
billed API call. See Chapter 25 Architecture Decision.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test-dummy-key-DO-NOT-USE-FOR-REAL-CALLS")
```

**Why this uses `setdefault`, not a hard overwrite**: if a developer genuinely wants to run a real-API smoke test locally (Architecture Handbook §11's "nightly smoke test" scenario), they can still export a real `GROQ_API_KEY` in their own shell before running `pytest`, and this line won't clobber it — `setdefault` only fills the gap when nothing is already set, matching the intended safety-net role without being an absolute, inflexible block.

### 10.3 `pytest.ini` (modified)

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
testpaths = ai/tests apps
python_files = test_*.py
addopts = -ra --reuse-db
```

**Why `--reuse-db`**: Django's test database is normally rebuilt from migrations on every single test run — reasonable for correctness, but slow once a project has 24+ chapters of migrations. `--reuse-db` keeps the test database between runs, only rebuilding it when migrations actually change (or when explicitly forced with `--create-db`) — a real, meaningful speed-up for a project this size, with no correctness cost as long as the flag's behavior is understood.

**Why `testpaths = ai/tests apps` (not just `.` for "everything")**: being explicit about exactly which two directory trees contain tests avoids `pytest` accidentally trying to collect from `config/`, `scripts/`, or anywhere else that was never meant to hold tests — a small guard against slow or confusing false-positive collection attempts.

### 10.4 `.coveragerc`

```ini
[run]
source = ai,apps
omit =
    */migrations/*
    */tests/*
    manage.py
    config/*

[report]
show_missing = True
fail_under = 85
```

**Why `config/*` is excluded from coverage**: settings files and URL configuration are declarative wiring, not logic with meaningful branches to exercise — counting them toward a coverage percentage would inflate the number without reflecting anything real about test quality, the same reasoning behind excluding migrations.

### 10.5 `apps/trips/tests/test_regressions.py`

```python
"""
Regression tests: one per previously-fixed bug, named after the
issue/ticket that reported it. NEVER delete a regression test once
added, even during a later refactor — if the code changes shape,
rewrite the test to still exercise the same underlying failure
mode, don't just remove it because it's inconvenient.

This file is a TEMPLATE — the example below is illustrative, not a
real historical bug from this project's development. Real
regression tests get added here (and in the equivalent file for
whichever app the bug belonged to) as real bugs are found and fixed
going forward.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.trips import services

User = get_user_model()


class TripRegressionTests(TestCase):
    def test_single_day_trip_start_equals_end_date_allowed(self):
        """
        Illustrative example: a trip where start_date == end_date (a
        single-day trip) must be allowed — validate_date_range() uses
        `end_date < start_date` (strictly less-than) as the rejection
        condition, not `<=`, specifically so a same-day trip is valid.
        This test guards against a future edit accidentally tightening
        that check to reject same-day trips.
        """
        user = User.objects.create_user(email="regression@example.com", password="pass1234")
        trip = services.create_trip(
            user=user, title="Day Trip", start_date=date(2026, 3, 1), end_date=date(2026, 3, 1),
        )
        self.assertEqual(trip.start_date, trip.end_date)
```

**Why this file exists even though this project has no real historical bug tickets to reference**: establishing the *convention* — the file name, the docstring format, the "never delete, only rewrite" rule — is the actual deliverable of this section. A real project adopting this Bible's patterns will have real bugs; this template is what the first one gets added to, in the correct place, with the correct shape, on day one rather than invented ad hoc when the first bug actually appears.

### 10.6 `requirements/dev.txt` (addition)

```
pytest-django
pytest-cov
```

### 10.7 `scripts/run_full_test_suite.sh`

```bash
#!/usr/bin/env bash
# The single command that runs EVERYTHING: ai/ and every Django app,
# with coverage enforced. Referenced by Chapter 28's CI/CD pipeline —
# CI runs exactly this script, nothing different or additional.
set -euo pipefail

echo "Running full test suite (ai/ + all Django apps) with coverage..."
pytest --cov=ai --cov=apps --cov-report=term-missing --cov-fail-under=85
```

**Why this script exists as a standalone file rather than only documenting the raw `pytest` command in this chapter's text**: Chapter 28's CI/CD pipeline needs to invoke *exactly* the same command a developer runs locally — a shared script, not a command copy-pasted separately into a CI config file and this chapter's docs, guarantees the two never quietly drift out of sync with each other.

---

## 11. Code Walkthrough

- **Zero existing test files needed to change for this chapter's consolidation to work** — this is worth stating plainly as the payoff of Section 2.2's technical detail: every `TestCase`-based test written across Chapters 3 through 24 runs completely unmodified under the new single `pytest` invocation, because `pytest-django`'s job was only ever "configure Django before collection," not "translate Django tests into some other format."
- **The `conftest.py` safety net (Section 10.2) is a defense-in-depth measure, not the primary safety mechanism**: the *primary* protection against real API calls in tests has been Chapters 11-20's disciplined mocking of `GroqClient` at every call site — this `conftest.py` addition is a backstop for the case where that discipline is accidentally broken somewhere, not a replacement for it.
- **`CELERY_TASK_ALWAYS_EAGER` quietly changes the *meaning* of tests that call `.delay()`** — worth being aware of, not just configuring: a test asserting `mock_delay.assert_called_once()` (Chapters 12, 17, 22's view tests) is checking that dispatch was *attempted*, using a mock that intercepts `.delay()` before eager execution would even apply; tests that let the real task run via eager mode (Chapter 25's own coverage of task bodies) are testing the task's *actual behavior*, a genuinely different thing being verified. Both styles coexist correctly in this project's test suite, and recognizing which one a given test is doing matters for understanding what it actually proves.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `pytest: error: unrecognized arguments: --reuse-db` | `pytest-django` not installed, or an old version | Confirm `pip install pytest-django` succeeded and check its version supports `--reuse-db` (it has for a long time — usually indicates a missing install, not a version issue) |
| Every Django-dependent test suddenly fails after this chapter | `DJANGO_SETTINGS_MODULE` in `pytest.ini` pointing at a settings module with an error, or a missing `test.py` file | Confirm `config/settings/test.py` exists and imports cleanly on its own: `python -c "import config.settings.test"` |
| A previously-passing AI agent test now fails with an authentication error | The `conftest.py` safety net is doing exactly what it's supposed to — the test wasn't actually mocking `GroqClient` and was relying on a real key being present | This is the safety net working correctly — go fix the test's mocking, don't work around the fake key |
| Coverage suddenly drops below 85% after this chapter, even though no app code changed | `.coveragerc`'s `omit` list doesn't match the actual project structure (e.g., migrations folder named differently) | Double check the `omit` glob patterns match real paths; run with `--cov-report=term-missing` to see exactly which lines are now "uncovered" |

---

## 13. Debugging

```bash
# 1. Confirm the consolidated run actually discovers BOTH test worlds
docker compose exec web pytest --collect-only -q | tail -20
# Should show both ai/tests/*.py AND apps/*/tests/*.py entries

# 2. Confirm CELERY_TASK_ALWAYS_EAGER is actually active during test settings
docker compose exec web python manage.py shell --settings=config.settings.test -c "
from django.conf import settings
print(settings.CELERY_TASK_ALWAYS_EAGER)
"

# 3. Confirm the GROQ_API_KEY safety net without running the whole suite
docker compose exec web python -c "
import conftest  # triggers the setdefault
import os
print(os.environ.get('GROQ_API_KEY'))
"
```

**Rollback strategy:** every change in this chapter is purely test-infrastructure — no migrations, no production code paths touched — so there is nothing to roll back beyond reverting these specific configuration files if something behaves unexpectedly.

---

## 14. Testing

This chapter's own "test" is the successful, single, consolidated run itself — there isn't new application logic to write unit tests *for*. What's verified here is that the *infrastructure* works correctly.

### 14.1 A structural check, run once to confirm the consolidation succeeded

```bash
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
```

Expected: every test from every prior chapter passes, in one run, with a single coverage report at the end.

### 14.2 `apps/core/tests/test_settings_sanity.py` (new — confirms `test.py` is actually in effect)

```python
"""
Sanity check that config.settings.test is genuinely the settings
module in effect during test runs — not accidentally falling back
to dev.py due to a misconfiguration.
"""
from django.conf import settings
from django.test import SimpleTestCase


class TestSettingsSanityCheck(SimpleTestCase):
    def test_celery_eager_mode_is_active(self):
        self.assertTrue(settings.CELERY_TASK_ALWAYS_EAGER)

    def test_debug_is_false_during_tests(self):
        self.assertFalse(settings.DEBUG)

    def test_password_hasher_is_the_fast_test_only_hasher(self):
        self.assertIn("MD5PasswordHasher", settings.PASSWORD_HASHERS[0])
```

### 14.3 `ai/tests/test_conftest_safety_net.py`

```python
"""
Confirms the root conftest.py's GROQ_API_KEY safety net is active.
"""
import os


def test_groq_api_key_is_set_to_a_safe_dummy_value():
    key = os.environ.get("GROQ_API_KEY")
    assert key is not None
    assert "test" in key.lower() or "dummy" in key.lower() or "DO-NOT-USE" in key
```

Run everything one final time to confirm the whole chapter holds together:

```bash
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing --cov-fail-under=85
```

---

## 15. Git Commit

```bash
git add config/settings/test.py conftest.py pytest.ini .coveragerc requirements/dev.txt apps/trips/tests/test_regressions.py scripts/run_full_test_suite.sh apps/core/tests/test_settings_sanity.py ai/tests/test_conftest_safety_net.py
git commit -m "chore(testing): consolidate ai/ and Django test suites into one pytest run

- pytest-django added; NO existing TestCase-based test needed to
  change — pytest has always been able to run unittest.TestCase
  subclasses natively, pytest-django's only job was configuring
  Django before collection (Chapter 25 Theory §2.2)
- config/settings/test.py: dedicated settings, never used for dev/
  prod — CELERY_TASK_ALWAYS_EAGER (no live worker needed for tests),
  fast password hasher, LocMemCache, locmem email backend,
  DEBUG=False deliberately (test prod-like error-handling behavior,
  not dev tracebacks)
- pytest.ini: testpaths now covers BOTH ai/tests and apps/, single
  invocation runs everything; --reuse-db for meaningful speed-up at
  this project's size
- Root conftest.py: GROQ_API_KEY safety net (setdefault, not
  overwrite) — any accidentally-unmocked GroqClient test now fails
  LOUDLY with an auth error instead of silently making a real,
  billed API call; defense-in-depth on top of, not instead of,
  Chapters 11-20's disciplined mocking
- .coveragerc: 85% threshold, migrations/tests/config excluded from
  the count (declarative wiring, not logic worth measuring)
- apps/trips/tests/test_regressions.py: establishes the regression-
  test convention (one file per app, one test per bug, never
  deleted) with a template example, per Architecture Handbook §11
- scripts/run_full_test_suite.sh: the exact command Chapter 28's
  CI will run — shared, not duplicated separately

Volume 7 begins. Chapter 25 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `pytest --cov=ai --cov=apps` runs the ENTIRE suite (ai/ + every Django app) in one invocation
- [ ] Zero existing test files were modified to make this work
- [ ] `config/settings/test.py` verified active via the sanity-check test (`CELERY_TASK_ALWAYS_EAGER`, `DEBUG=False`, fast hasher)
- [ ] Root `conftest.py`'s `GROQ_API_KEY` safety net verified present
- [ ] Coverage threshold (`fail_under = 85`) configured; migrations/tests/config excluded from the count
- [ ] `apps/trips/tests/test_regressions.py` establishes the convention with a working example
- [ ] `scripts/run_full_test_suite.sh` runs successfully standalone
- [ ] All tests passing, coverage at or above threshold
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 26 — Security Hardening Pass** audits every security-relevant decision made incrementally across the previous 25 chapters — JWT configuration (Chapter 4), rate limiting (Chapter 17), the single public endpoint (Chapter 21), prompt-injection defenses implied but not yet formally tested (Architecture Handbook §12) — and closes any gaps found, with the newly-consolidated test suite from this chapter as the tool used to prove each fix. Say **"Continue to Chapter 26"** when ready.
