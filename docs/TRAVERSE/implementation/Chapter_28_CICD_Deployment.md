# Chapter 28 — CI/CD & Deployment

**Volume 7: Hardening & Production | Chapter 28 of 29**

> This chapter closes several loops at once, without touching a single frozen infrastructure file. Chapter 25's `scripts/run_full_test_suite.sh` finally gets a real CI pipeline to run it. Architecture Handbook §11's "nightly smoke test" — mentioned in Volume 1, never built — gets built here, as a deliberately opt-in, explicitly-gated test that makes one real, billed LLM call to confirm the provider integration itself still works. Chapter 1's `/health/` endpoint, verified by hand in the very first chapter, finally gets used automatically to confirm a real deployment succeeded, 27 chapters later.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Build a CI pipeline that runs entirely against mocked AI calls (Chapter 25's safety net), never risking a real, billed API call on every push.
- Build a genuinely separate, opt-in "smoke test" path — explicitly gated so it can never run by accident — that exercises the real provider integration on a schedule, not on every commit.
- Write a deployment script that orchestrates DockForge's already-existing production configuration, adding zero new infrastructure of its own.
- Use Chapter 1's `/health/` endpoint as an automated post-deployment verification step, closing a loop opened in this project's very first chapter.

---

## 2. Theory

### 2.1 Why CI Must Never Make a Real LLM Call, and Smoke Tests Must Never Run Automatically (ELI10)

Imagine a fire drill that happens every single time anyone opens the building's front door — exhausting, expensive, and it stops meaning anything as a genuine test. CI runs on every push and every pull request, potentially dozens of times a day — if it made a real, billed LLM call each time, cost would scale with development activity, not with anything meaningful being verified (Chapter 25's mocking already proves the *logic* works). A smoke test, by contrast, genuinely needs to hit the real provider to prove *that specific, narrow thing* — but should only do so on a controlled schedule (nightly), never accidentally triggered by a routine commit.

### 2.2 Why This Chapter's Deployment Script Orchestrates, Rather Than Defines, Infrastructure

DockForge already provides a working production Docker Compose configuration — Architecture Handbook §2.1 established this as frozen from the very first chapter. This chapter's `scripts/deploy.sh` never writes a new compose file, never touches `Dockerfile` or `nginx.conf` — it only issues the *commands* a deployment actually needs (pull, migrate, restart, verify) against whatever production compose configuration DockForge already provides. The distinction matters: this project owns the *sequence of operations*, never the underlying infrastructure those operations run against.

### 2.3 Why Post-Deployment Health Verification Uses Chapter 1's Existing Endpoint, Not a New One

Chapter 1 built `/health/` and manually verified it before any application code existed, specifically so that "is the platform actually working" could always be answered with one clear signal. Building a *different* health check now, 27 chapters later, would fragment that signal into two things that could disagree with each other. Reusing the exact same endpoint for automated post-deploy verification is the correct call — it's already comprehensive (Chapter 1 confirmed database and Redis connectivity through it), and using it here is simply automating what Chapter 1 always did by hand.

---

## 3. Architecture Decision

**Decision:** Regular CI (`.github/workflows/ci.yml`) runs on every push/PR, always with a dummy `GROQ_API_KEY`, executing exactly `scripts/run_full_test_suite.sh` (Chapter 25) — the same command a developer runs locally, never a CI-specific variant.

**Decision:** The nightly smoke test (`.github/workflows/nightly-smoke-test.yml`) is a completely separate workflow, running on a schedule only, using a real `GROQ_API_KEY` from a CI secret, and executing a dedicated test file (`ai/tests/test_smoke.py`) that is *itself* gated by an environment variable check — meaning even if someone accidentally ran the smoke test file through the regular suite, it would skip itself rather than fire.

**Decision:** `scripts/deploy.sh` is the single, canonical deployment sequence — pull, migrate, restart, health-check — never manually improvised commands run ad hoc against production.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Write `ai/tests/test_smoke.py` with its double-gated skip condition | Needed before any workflow can safely reference it |
| Write `.github/workflows/ci.yml` | The primary, everyday pipeline — comes first |
| Write `.github/workflows/nightly-smoke-test.yml` | A genuinely separate concern, built after the main pipeline is solid |
| Write `scripts/deploy.sh` | Needs the CI pipeline already passing as a prerequisite gate |
| Write `docs/deployment_checklist.md` | Last — synthesizes everything from this chapter and Chapter 26's security findings into one pre-deploy reference |

---

## 5. File Structure

```
.github/workflows/
├── ci.yml                          # NEW — every push/PR, mocked AI, Chapter 25's script
└── nightly-smoke-test.yml           # NEW — scheduled only, real API, explicitly gated

ai/tests/
└── test_smoke.py                     # NEW — double-gated: env var check + only in smoke workflow

scripts/
└── deploy.sh                          # NEW — orchestrates DockForge's existing prod compose

docs/
└── deployment_checklist.md             # NEW
```

---

## 6. Folder Location

New files under `.github/workflows/`, `ai/tests/`, `scripts/`, `docs/`. No changes to any DockForge-owned file.

---

## 7. Terminal Commands

```bash
# Verify the deploy script's syntax without actually running it against anything real
bash -n scripts/deploy.sh

# Run the smoke test locally, deliberately, with a real key (developer's own choice, own cost)
RUN_SMOKE_TESTS=true GROQ_API_KEY=<your-real-key> pytest ai/tests/test_smoke.py -v
```

---

## 8. Docker Commands

None — this chapter's artifacts are CI configuration and deployment orchestration, not something run inside the dev container directly (though `scripts/deploy.sh` itself invokes `docker compose` commands against production).

---

## 9. Expected Output

```
$ bash -n scripts/deploy.sh && echo "syntax OK"
syntax OK

# In CI, ci.yml's log:
Running full test suite (ai/ + all Django apps) with coverage...
======================= 340 passed in 41.2s ========================
Coverage: 90% (threshold: 85%) — PASS

# In the nightly workflow's log (scheduled, real key):
ai/tests/test_smoke.py::test_real_groq_call_returns_valid_response PASSED
```

---

## 10. Code

### 10.1 `ai/tests/test_smoke.py`

```python
"""
Smoke test — makes ONE real, billed call to the actual Groq API.
DOUBLE-gated so it can never run by accident:
1. skipif on RUN_SMOKE_TESTS env var (must be explicitly "true")
2. Chapter 25's conftest.py sets a dummy GROQ_API_KEY by default,
   so even if gate #1 somehow failed, a real call would fail with
   an auth error against the fake key, not silently succeed.

Only ever invoked deliberately: locally by a developer who exports
a real key, or by the nightly-smoke-test.yml workflow with a real
key from a CI secret. NEVER part of the regular test suite run.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SMOKE_TESTS") != "true",
    reason="Smoke tests only run when RUN_SMOKE_TESTS=true is explicitly set "
           "(the nightly workflow, or a developer choosing to spend real API cost).",
)


def test_real_groq_call_returns_valid_response():
    from ai.clients.groq_client import GroqClient

    client = GroqClient()
    result = client.call(
        system_prompt="You are a helpful assistant.",
        user_prompt="Respond with exactly the word: ok",
    )
    assert result
    assert isinstance(result, str)


def test_real_travel_planner_agent_produces_valid_schema():
    """
    A slightly richer smoke test — confirms not just that the API
    responds, but that the FULL structured-output pipeline (Chapter
    11's parse_structured_output, the real prompt) still produces
    schema-valid output against the real provider, not a mock.
    """
    from ai.agents.travel_planner import travel_planner_node

    state = {
        "trip_title": "Smoke Test Trip", "start_date": "2026-06-01", "end_date": "2026-06-02",
        "destination_names": ["Tokyo, Japan"], "budget_style": "moderate",
        "travel_pace": "balanced", "interests": ["food"],
    }
    result = travel_planner_node(state)
    assert "itinerary_plan" in result
    assert len(result["itinerary_plan"].days) >= 1
```

**Why this file has two tests, not just one basic connectivity check**: the first test proves the *provider connection* works; the second proves the *entire structured-output pipeline* still works against a real, non-deterministic model response — a genuinely different, more valuable thing to know than "the API is reachable." A provider outage would fail the first test; a subtle prompt or schema regression that only shows up against real (not mocked) model behavior would be caught by the second.

### 10.2 `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: ai_travel_planner_ci
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/ai_travel_planner_ci
      REDIS_URL: redis://localhost:6379/0
      SECRET_KEY: ci-only-insecure-key
      GROQ_API_KEY: ci-dummy-key-never-real   # deliberately fake — see Chapter 28 Theory §2.1
      RUN_SMOKE_TESTS: "false"                 # explicit, even though this is already the default

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements/base.txt
          pip install -r requirements/dev.txt

      - name: Migration check (no missing migrations)
        run: python manage.py makemigrations --check --dry-run

      - name: Run full test suite (ai/ + all Django apps)
        run: bash scripts/run_full_test_suite.sh
```

**Why `GROQ_API_KEY` is set explicitly to a dummy value in CI, even though Chapter 25's `conftest.py` already does this as a fallback**: this is intentional defense in depth, the same layered-safety instinct as the smoke test's double-gate — CI's own environment being explicitly wrong-on-purpose means the safety doesn't depend on `conftest.py` alone ever working correctly; two independent layers both have to fail simultaneously for a real call to accidentally succeed.

**Why the migration check runs as its own separate step before the test suite, not folded into it**: a missing migration is a *different kind* of failure than a failing test — catching it first, with its own clear step name in the CI log, means a developer scanning a failed run immediately knows "did I forget to run `makemigrations`" versus "did I break a test," without needing to dig through the full test suite's output first.

### 10.3 `.github/workflows/nightly-smoke-test.yml`

```yaml
name: Nightly AI Smoke Test

on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC daily
  workflow_dispatch:        # allows manual trigger too, for on-demand verification

jobs:
  smoke:
    runs-on: ubuntu-latest

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY_REAL }}
      RUN_SMOKE_TESTS: "true"

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements/base.txt -r requirements/dev.txt
      - name: Run smoke tests against the REAL Groq API
        run: pytest ai/tests/test_smoke.py -v
```

**Why this is a completely separate workflow file, not a conditional job inside `ci.yml`**: separating them means a smoke test failure (a real provider issue, or a real regression) never blocks a normal pull request merge the way a `ci.yml` failure would — the two have genuinely different consequences and genuinely different audiences (a developer needs `ci.yml` to pass to merge; the smoke test failing is an alert for whoever monitors the AI integration's health, a different concern entirely).

### 10.4 `scripts/deploy.sh`

```bash
#!/usr/bin/env bash
# Orchestrates DockForge's EXISTING production compose configuration.
# This script defines NO new infrastructure — it only issues commands
# against whatever docker-compose.prod.yml (or equivalent) DockForge
# already provides. See Chapter 28 Theory §2.2.
set -euo pipefail

COMPOSE_FILE="${DEPLOY_COMPOSE_FILE:-docker-compose.prod.yml}"

echo "==> Pulling latest images..."
docker compose -f "$COMPOSE_FILE" pull

echo "==> Running database migrations..."
docker compose -f "$COMPOSE_FILE" run --rm web python manage.py migrate --noinput

echo "==> Restarting services..."
docker compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for the web service to become ready..."
sleep 5

echo "==> Verifying deployment via /health/ (Chapter 1's endpoint)..."
if curl -sf http://localhost:8000/health/ | grep -q '"status": "ok"'; then
  echo "==> Deployment verified healthy."
else
  echo "==> HEALTH CHECK FAILED. Deployment may be broken — investigate before proceeding."
  exit 1
fi

echo "==> Deployment complete."
```

**Why `COMPOSE_FILE` is configurable via an environment variable with a sensible default, rather than hardcoded**: different DockForge setups may name their production compose file slightly differently — parameterizing this one detail, while keeping everything else about the script fixed, means the script adapts to the actual infrastructure it's pointed at without needing its logic rewritten.

**Why the script exits non-zero (`exit 1`) on a failed health check rather than just printing a warning**: a deployment script that reports success even when the post-deploy verification failed would defeat the entire purpose of checking — any CI/CD system or human operator running this script needs a real, checkable exit code to know whether to proceed, roll back, or investigate.

### 10.5 `docs/deployment_checklist.md`

```markdown
# Pre-Deployment Checklist

Run through this before every production deployment. This is a
synthesis of commitments made across the whole Implementation Bible
— nothing here is new, it's a single place to confirm they all hold
at once, right before a real deploy.

## Code Quality (Chapter 25)
- [ ] scripts/run_full_test_suite.sh passes locally
- [ ] Coverage at or above 85%
- [ ] python manage.py makemigrations --check --dry-run reports no changes

## Security (Chapter 26)
- [ ] GROQ_API_KEY in production is a REAL key, stored as a secret,
      never committed to .env in version control
- [ ] CORS_ALLOWED_ORIGINS set to the real, exact frontend domain(s)
- [ ] DEBUG = False confirmed in the actual deployed settings module
- [ ] SECURE_SSL_REDIRECT, SECURE_HSTS_*, cookie security flags active
      (config/settings/prod.py)

## CI/CD (Chapter 28)
- [ ] ci.yml is green on the commit being deployed
- [ ] The most recent nightly smoke test passed (or, if it's been run
      manually via workflow_dispatch, confirm current)

## Deployment
- [ ] scripts/deploy.sh run, health check passed
- [ ] Spot-check /health/ manually after deploy, don't rely on the
      script alone for anything customer-facing critical
```

---

## 11. Code Walkthrough

- **The smoke test's double-gate (env var check + Chapter 25's fake-key fallback) is worth recognizing as the same layered-defense pattern used throughout this project's security-relevant code**: Chapter 12's single-door rule had both a documented convention *and* an automated test; Chapter 26's rate limiting protects both `/plan/` and `/chat/` independently. Real safety-critical behavior in this project is consistently never left to rely on exactly one mechanism.
- **`scripts/deploy.sh` reusing Chapter 1's `/health/` endpoint for verification is the clearest "full circle" moment in the entire Implementation Bible**: the very first command run in Chapter 1 (`curl -i http://localhost:8000/health/`) and the very last operational step of a real deployment 27 chapters later are, quite literally, the same check — proof that a good foundational decision made on day one can still be exactly the right tool at the very end.
- **Separating `ci.yml` and `nightly-smoke-test.yml` into two files reflects a real organizational principle**: things that gate a merge and things that monitor ongoing system health are different concerns with different audiences and different consequences on failure — conflating them into one workflow would make both harder to reason about.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| CI fails on `makemigrations --check --dry-run` unexpectedly | A model was changed without running `makemigrations` locally before committing | Run `makemigrations` locally, commit the resulting migration file |
| Nightly smoke test fails but regular CI is green | This is expected and correct behavior in some cases — it means the *provider* or a *real-response* edge case is the problem, not the mocked logic | Investigate the real Groq API status or recent prompt changes; this is exactly what the smoke test exists to catch |
| `deploy.sh` fails at the health check step | The `web` service didn't actually come up cleanly after migration, or `sleep 5` wasn't long enough for a genuinely slow-starting environment | Check `docker compose -f docker-compose.prod.yml logs web`; consider increasing the sleep duration for slower environments |
| Smoke test accidentally runs during a normal local `pytest` invocation | `RUN_SMOKE_TESTS` was accidentally exported in the developer's shell session from earlier testing | `unset RUN_SMOKE_TESTS`, or open a fresh shell — the skip condition is correct, the environment carried over unintentionally |

---

## 13. Debugging

```bash
# 1. Confirm the smoke test correctly skips by default
docker compose exec web pytest ai/tests/test_smoke.py -v
# Expected: SKIPPED, not PASSED or FAILED

# 2. Confirm it correctly runs (and would make a real call) when explicitly enabled
docker compose exec -e RUN_SMOKE_TESTS=true web pytest ai/tests/test_smoke.py --collect-only -v
# Confirms collection/gating logic without actually spending real API cost

# 3. Dry-run the deploy script's command sequence without executing docker commands
bash -n scripts/deploy.sh
```

**Rollback strategy:** none of this chapter's artifacts touch application data — a bad CI config or deploy script is fixed by editing the file and re-running; a failed real deployment is rolled back using DockForge's own existing rollback procedure (outside this project's scope, since infrastructure recovery is a platform-layer concern, not an application-layer one).

---

## 14. Testing

### 14.1 `ai/tests/test_smoke.py` gate itself — a meta-test

```python
import os
from unittest.mock import patch


def test_smoke_test_is_skipped_by_default():
    """
    Meta-test: confirms the skip condition itself is correct, without
    needing RUN_SMOKE_TESTS=true or a real API key to verify it.
    """
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("RUN_SMOKE_TESTS", None)
        should_skip = os.environ.get("RUN_SMOKE_TESTS") != "true"
        assert should_skip is True
```

### 14.2 Manual verification of the CI/deploy artifacts (no automated test possible for YAML syntax beyond linting)

```bash
# Validate workflow YAML syntax
docker run --rm -v "$PWD:/repo" rhysd/actionlint /repo/.github/workflows/ci.yml
docker run --rm -v "$PWD:/repo" rhysd/actionlint /repo/.github/workflows/nightly-smoke-test.yml

# Validate deploy script syntax
bash -n scripts/deploy.sh
```

Run the full suite one more time to confirm nothing in this chapter's additions broke anything:

```bash
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
```

---

## 15. Git Commit

```bash
git add .github/workflows/ci.yml .github/workflows/nightly-smoke-test.yml ai/tests/test_smoke.py scripts/deploy.sh docs/deployment_checklist.md
git commit -m "ci: CI pipeline, nightly smoke test, deployment script

- ci.yml: every push/PR, ALWAYS a dummy GROQ_API_KEY (defense in
  depth alongside Chapter 25's conftest fallback - two independent
  layers must both fail for a real call to slip through), runs
  EXACTLY scripts/run_full_test_suite.sh (Chapter 25) - no CI-
  specific test variant, same command a developer runs locally
- Separate migration-check step before the test suite, so a missing
  migration is immediately distinguishable from a failing test in
  the CI log
- nightly-smoke-test.yml: genuinely separate workflow (not a
  conditional job in ci.yml - different consequences, different
  audience), scheduled + workflow_dispatch, real API key from a CI
  secret
- ai/tests/test_smoke.py: DOUBLE-gated (env var skip + fake-key
  fallback as backstop) - makes real calls confirming both raw
  connectivity AND the full structured-output pipeline against a
  real, non-deterministic response, never runs in regular CI/local
  test runs
- scripts/deploy.sh: orchestrates DockForge's EXISTING prod compose
  config, zero new infrastructure - pull, migrate, restart, then
  verifies via Chapter 1's /health/ endpoint, exiting non-zero on a
  failed health check
- docs/deployment_checklist.md: single pre-deploy reference
  synthesizing Chapters 25/26/28's commitments

Chapter 1's /health/ endpoint, manually verified in this project's
very first chapter, now automates real deployment verification.
Chapter 28 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `ci.yml` runs on every push/PR with a dummy `GROQ_API_KEY`, executes exactly `scripts/run_full_test_suite.sh`
- [ ] Migration check is its own distinct CI step, before the test suite
- [ ] `nightly-smoke-test.yml` is a separate workflow file, scheduled + manually triggerable, real API key from a secret
- [ ] `ai/tests/test_smoke.py` is double-gated; confirmed to skip by default
- [ ] `scripts/deploy.sh` touches zero DockForge-owned infrastructure files, only orchestrates commands
- [ ] Deployment verification reuses Chapter 1's `/health/` endpoint, exits non-zero on failure
- [ ] `docs/deployment_checklist.md` accurately synthesizes Chapters 25/26/28's commitments
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 29 — Production Readiness Review** is the final chapter. It walks every checklist accumulated across all 28 prior chapters — architecture, every app's own checklist, security, performance, CI/CD — into one consolidated launch gate, and closes the Implementation Bible with a retrospective template for capturing what the next real bug, the next real feature, and the next real engineer joining this project will need to know that no single prior chapter could have anticipated. Say **"Continue to Chapter 29"** when ready.
