# Chapter 28 — CI/CD & Deployment Checklist

This checklist is adapted to the current TraVerse repository contracts.

## 1. CI

- [ ] `.github/workflows/ci.yml` runs on pushes and pull requests to `main`.
- [ ] CI uses `backend/requirements/base.txt` and `backend/requirements/development.txt`.
- [ ] CI runs `python manage.py check`.
- [ ] CI runs `python manage.py makemigrations --check --dry-run`.
- [ ] CI runs the authoritative full Django suite: `python manage.py test -v 1`.
- [ ] CI never requires or calls the real Groq provider.

## 2. Nightly AI smoke test

- [ ] Repository variable `ENABLE_AI_SMOKE_TEST` is set to `true` only when the smoke test is intentionally enabled.
- [ ] Repository secret `GROQ_API_KEY` is configured before enabling the smoke test.
- [ ] The smoke test uses the current `TravelPlannerAgent` / `PlanningGraphState` contract.
- [ ] The smoke test validates that a non-empty itinerary is returned.
- [ ] Provider credentials are never committed to Git.

## 3. Production deployment

- [ ] `infrastructure/env/production.env` exists on the deployment host and is not committed.
- [ ] `docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/compose/docker-compose.prod.yml config` succeeds.
- [ ] PostgreSQL and Redis are healthy.
- [ ] The `django` service is healthy.
- [ ] Migrations complete successfully.
- [ ] Static files are collected successfully.
- [ ] `/health/` returns HTTP 200 and `"status": "healthy"`.
- [ ] Final service status is healthy after restart.

## 4. Repository-specific invariants

- [ ] Do not introduce a `web` Compose service; TraVerse uses `django`.
- [ ] Do not introduce `config.settings.test`; CI uses the existing `config.settings` with CI environment variables.
- [ ] Do not change `/health/` to return `"ok"`; deployment consumes the existing `"healthy"` contract.
- [ ] Do not create a second infrastructure stack for deployment.
- [ ] Keep the real-provider smoke test isolated from normal CI.

## 5. Baseline verification

Chapter 27 established the current regression baseline as 391 Django tests passing with zero failures/errors and zero Django system-check issues. Any Chapter 28 implementation must preserve that baseline.
