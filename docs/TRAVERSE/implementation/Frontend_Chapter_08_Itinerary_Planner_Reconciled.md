# Frontend Chapter 8 — Itinerary Planner UI Reconciled

## Pre-implementation audit

- Target chapter: Chapter 8, Itinerary — Day-by-Day Planner UI.
- Current branch: `work`.
- Previous completed chapter: Frontend Chapter 7 trips dashboard/CRUD reconciliation.
- Backend domain: `apps.itinerary`.
- Backend URLs: `GET /api/itinerary/trips/<uuid:trip_id>/itinerary/` and `POST /api/itinerary/itinerary-days/<uuid:day_id>/items/`.
- Backend identifiers: trip, day, item, and destination identifiers are UUID strings.
- Backend response shape: trip itinerary retrieval returns a plain array of itinerary day objects. Each day has nested, ordered items.
- Backend write shape: adding an item requires `title` and accepts optional `description`, `start_time`, `estimated_cost_usd`, and `destination_id`. Ordering is controlled by the backend service.
- Existing frontend architecture: trip detail already lives at `/trips/:tripId`; server state flows through feature hooks and `apiRequest()`; shared UI primitives are available under `src/components/ui`.
- Backend changes required: no.

## Reconciliation notes

| Original/source assumption | Actual repository behavior | Chosen implementation |
| --- | --- | --- |
| The original backend chapter sample showed `/api/v1/trips/<trip_id>/itinerary/`. | Current URL config mounts itinerary under `/api/itinerary/`, producing `/api/itinerary/trips/<uuid:trip_id>/itinerary/`. | The frontend itinerary API calls the current backend path exactly. |
| The sample output wrapped days in a `{ "days": [...] }` object. | Current `TripItineraryView` returns `serializer.data` directly, so the response is a plain array. | The API boundary models `ItineraryDay[]`; no backend pagination or envelope was invented. |
| Chapter text discusses reorder service behavior. | Current backend only exposes read itinerary and append-item endpoints. No reorder endpoint exists. | The UI only reads days and appends items. It does not fabricate reordering behavior. |
| A complete itinerary might be expected immediately after trip creation. | Current trip creation does not create itinerary days, and there is no frontend-safe endpoint to create days manually. | The UI shows an explicit empty state when no itinerary days exist and waits for existing/AI-generated days. |

## Implementation summary

- Added a feature API module for itinerary read and append-item endpoints.
- Added TanStack Query hooks for trip itinerary retrieval and add-item mutation invalidation.
- Added a trip detail itinerary panel that preserves the existing trip detail route and workspace layout.
- Added tests covering API paths, guarded query behavior, empty states, validation, and mutation payloads.

## Regression notes

No backend files were changed. The trip detail page now mounts the itinerary panel and keeps budget/recommendations as future surfaces. Existing trip, destination, profile, auth, and shared UI behavior remains behind the same routes and API client boundary.
