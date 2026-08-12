# Backend Chapter 10 — `recommendations` App (Reconciled)

**Volume 3: Trip Sub-Domains | Chapter 10 of 29**

## Pre-implementation audit

- The source chapter defines recommendations as read-mostly, AI-populated data with a user accept/reject workflow; the actual Recommendation Agent is intentionally deferred to Chapter 15.
- The repository already contained a `recommendations` app, model, selectors, services, serializers, views, URLs, admin, migration, and a development-only `seed_fake_recommendations` command.
- The repository's current contract differs from the illustrative chapter in several important ways: recommendation IDs are UUIDs, the model uses `reason` instead of `title`/`description`, categories are `restaurant`, `attraction`, `hotel`, `shopping`, `experience`, and `hidden_gem`, scores use two decimal places, and the API is mounted at `/api/recommendations/`.
- Therefore this implementation follows the Codex reconciliation strategy used for the previous chapters: preserve real repository contracts, make only the missing Chapter 10 behavior changes, and do not introduce a breaking schema migration merely to copy illustrative sample code.

## Reconciliation decisions

| Source chapter assumption | Current repository behavior | Implementation decision |
| --- | --- | --- |
| Integer recommendation IDs. | UUID primary keys. | Preserve UUIDs. |
| `title`/`description` recommendation fields. | `destination` + `reason`. | Preserve the existing domain model. |
| Example categories such as `activity` and `event`. | Existing categories are `restaurant`, `attraction`, `hotel`, `shopping`, `experience`, `hidden_gem`. | Preserve the existing enum. |
| Three-decimal score. | Two-decimal score already migrated. | Preserve the existing persisted contract. |
| `/api/v1/trips/<trip_id>/recommendations/`. | `/api/recommendations/trips/<trip_id>/recommendations/`. | Preserve the current URL contract. |
| Simple status assignment. | Existing accept/reject services directly assign status. | Add the explicit transition table: `pending -> accepted/rejected`; both terminal. |
| No status filter required by the existing implementation. | Selectors already support pending/accepted/rejected. | Add optional `?status=` filtering to the trip list endpoint. |
| Fake seed command must be added. | Command already exists. | Preserve it and add regression coverage. |

## Implementation

### State machine

`RecommendationStatus.PENDING` may transition to either `ACCEPTED` or `REJECTED`. Both terminal states have no outgoing transitions. A second decision raises `InvalidRecommendationTransition`, which inherits from the project's `BusinessRuleViolation` and therefore uses the existing global DRF exception handler rather than introducing a new response mechanism.

### API behavior

- `GET /api/recommendations/trips/<uuid:trip_id>/recommendations/`
- Optional `?status=pending|accepted|rejected`
- `POST /api/recommendations/recommendations/<uuid:recommendation_id>/accept/`
- `POST /api/recommendations/recommendations/<uuid:recommendation_id>/reject/`

Trip and recommendation access remains scoped to the authenticated user's owned trip. Cross-user access continues to return 404, matching the existing project convention.

### Seed command

`seed_fake_recommendations <trip_id> --count N` remains explicitly development-only and trip-scoped. It uses linked trip destinations first and falls back to active catalog destinations when the trip has none.

## Files changed

- `backend/apps/recommendations/services.py`
- `backend/apps/recommendations/views.py`
- `backend/apps/recommendations/tests/test_services.py`
- `backend/apps/recommendations/tests/test_views.py`
- `backend/apps/recommendations/tests/test_management_commands.py`
- this reconciled implementation document

No model migration was required.

## Verification plan

- Focused: `python manage.py test apps.recommendations -v 2`
- Full backend suite after the focused tests pass.
- Django system checks/migration checks according to the repository's normal CI workflow.
- Confirm no AI/LLM generation logic was introduced; Chapter 10 remains the data/API foundation for the later Recommendation Agent.
