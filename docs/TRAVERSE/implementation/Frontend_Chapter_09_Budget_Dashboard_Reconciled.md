# Frontend Chapter 9 — Budget Dashboard UI (Reconciled)

## Pre-implementation audit

- Previous completed frontend feature: itinerary planner UI.
- Backend domain: `backend/apps/budget`.
- Backend URL mount: `/api/budget/`.
- Backend endpoints used:
  - `GET /api/budget/trips/<uuid:trip_id>/budget/`
  - `POST /api/budget/trips/<uuid:trip_id>/budget/items/`
- Both endpoints require authentication and scope the trip lookup to `user=request.user`.
- `BudgetSerializer` returns `id`, `currency`, `planned_total`, `computed_total`, and nested `line_items`.
- `CreateBudgetLineItemSerializer` accepts `category`, `description`, `amount`, and optional `is_ai_estimated`.
- The frontend sends only manual-user fields for line-item creation; the backend default keeps `is_ai_estimated` false.

## Reconciliation decisions

| Original/source assumption | Actual repository behavior | Chosen implementation |
| --- | --- | --- |
| Budget APIs may live under `/api/v1/trips/<id>/budget/`. | Current backend exposes `/api/budget/trips/<uuid:trip_id>/budget/`. | Use the current `/api/budget/` paths exactly. |
| Budget may have a dedicated dashboard route. | Trip detail is already the established surface for trip sub-domain panels. | Mount `TripBudgetPanel` in `TripDetailPage`. |
| Budget editing may include full CRUD or planned-total editing. | Current backend exposes budget read and line-item create only. | Implement read plus append-only manual line-item creation; do not invent unsupported endpoints. |
| The UI may use charts. | No charting dependency exists and the current frontend favors shared primitives. | Render category totals with existing `Card` components rather than adding a dependency. |

## Implementation

- Added a typed budget API boundary using the shared `apiRequest()` gateway.
- Added TanStack Query hooks for guarded budget fetching and line-item creation.
- Invalidated the trip budget query after a successful line-item mutation so computed totals and line items refresh from the backend source of truth.
- Added `TripBudgetPanel` with computed/planned totals, line-item count, category totals, line-item display, loading/error/empty states, local validation, and a backend-compatible add-item form.
- Mounted the panel into the existing trip detail page and removed Budget from the future-feature placeholder.
- Added API-boundary and component tests.

## Backend changes

None. The existing backend contract is sufficient for the frontend budget workflow, so no backend behavior was invented or changed.

## Verification

- Targeted budget API and panel tests pass.
- Full frontend test suite passes.
- Production build passes.
- `git diff --check` passes.
