# Frontend Chapter 10 — Recommendations UI (Reconciled)

## Pre-implementation audit

- Previous completed frontend feature: Chapter 9 budget dashboard.
- The existing frontend already uses the trip detail page as the established surface for trip sub-domain panels: itinerary first, then budget.
- `frontend/src/features/recommendations/` exists as a reserved empty feature boundary, so no new top-level domain structure was invented.
- The current backend recommendation serializer returns: `id`, `category`, `score`, `reason`, `status`, `is_ai_generated`, `destination`, and `created_at`.
- The current backend recommendation list endpoint is `/api/recommendations/trips/<uuid:trip_id>/recommendations/` and currently returns a plain JSON array rather than DRF's pagination envelope.
- The current backend exposes separate POST endpoints for accepting and rejecting recommendations.
- The frontend already has the shared `PaginatedResponse<T>` type and the destination feature already demonstrates the correct reconciliation pattern: normalize a current plain-array backend response at the API boundary while keeping the feature internals on the shared list shape.
- `recommendationStatusColors` already exists in the shared status-color map, so no duplicate status styling was introduced.

## Reconciliation decisions

| Original/expected frontend assumption | Actual repository behavior | Chosen implementation |
| --- | --- | --- |
| Recommendations can be a standalone routed page. | Current route configuration does not expose a recommendations route, while trip detail is already the established sub-domain surface. | Implement `TripRecommendationsPanel` and mount it in `TripDetailPage`, matching Chapters 8 and 9. |
| The list endpoint may return `{count,next,previous,results}`. | Current endpoint returns a plain array. | Normalize either an array or a paginated response inside `recommendationsApi.ts`; the rest of the feature uses `PaginatedResponse<Recommendation>`. |
| Recommendation records may contain title/description. | Current serializer provides destination + reason. | Render the actual destination name/location and `reason`; do not invent unsupported fields. |
| Status filtering can be server-side. | Current backend list view has no status query parameter. | Filter the already-fetched trip recommendations locally; do not modify backend behavior merely for frontend convenience. |
| Accept/reject may need new backend behavior. | Existing endpoints already support both actions. | Consume the existing POST endpoints through TanStack Query mutations and invalidate the trip recommendation query after success. |
| Recommendation cards may require a new UI system. | Existing shared `Card`, `Button`, `StatusBadge`, `Spinner`, `ErrorState`, and `EmptyState` primitives are sufficient. | Reuse the existing design system; no new dependency or primitive was added. |

## Implementation

### API boundary

- `fetchTripRecommendations(tripId)` calls the current backend URL and normalizes the response.
- `acceptRecommendation(recommendationId)` calls the existing accept endpoint.
- `rejectRecommendation(recommendationId)` calls the existing reject endpoint.
- Recommendation and destination response types mirror the actual serializer contract.

### Query/mutation layer

- `useTripRecommendations` provides the cached read query.
- `useAcceptRecommendation` performs an accept mutation and invalidates the trip recommendation query on success.
- `useRejectRecommendation` performs a reject mutation and invalidates the trip recommendation query on success.
- No manual local status mutation is used as the source of truth; the backend response is re-fetched after a successful decision.

### UI

`TripRecommendationsPanel` provides:

- loading, error, and empty states;
- recommendation category and AI-generated indicators;
- destination name and location;
- human-readable recommendation reason;
- relevance score rendered as a percentage match;
- pending/accepted/rejected status badge;
- local All/Pending/Accepted/Rejected filters;
- accept and reject controls only for pending recommendations;
- mutation-specific loading and error feedback;
- responsive destination imagery when the backend supplies `image_url`.

The panel is mounted after the itinerary and budget panels in `TripDetailPage`. The old "Recommendations" future-feature placeholder is removed because the feature is now real.

## Backend changes

**None.** The current backend contract already exposes all data and actions required by this frontend chapter. No backend modification is justified merely to make the frontend implementation more convenient.

## Files changed

- `frontend/src/features/recommendations/api/recommendationsApi.ts`
- `frontend/src/features/recommendations/hooks/useTripRecommendations.ts`
- `frontend/src/features/recommendations/hooks/useAcceptRecommendation.ts`
- `frontend/src/features/recommendations/hooks/useRejectRecommendation.ts`
- `frontend/src/features/recommendations/components/TripRecommendationsPanel.tsx`
- `frontend/src/features/recommendations/__tests__/recommendationsApi.test.ts`
- `frontend/src/features/recommendations/__tests__/TripRecommendationsPanel.test.tsx`
- `frontend/src/features/trips/pages/TripDetailPage.tsx`
- this reconciliation document

## Verification plan

- Targeted API-boundary tests must verify the exact current backend URLs and payloads.
- Component tests must verify rendering, local status filtering, accept/reject actions, and terminal-state UI behavior.
- Full frontend Vitest suite must pass.
- Production TypeScript/Vite build must pass.
- `git diff --check` must pass.
- No backend file should appear in the Chapter 10 frontend diff.
