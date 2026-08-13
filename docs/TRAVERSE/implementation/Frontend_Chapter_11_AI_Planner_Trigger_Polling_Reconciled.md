# Frontend Chapter 11 — AI Planner Trigger & Polling Reconciliation

## Original chapter intent

Implement the frontend entry point for asynchronous AI trip planning and represent the planner's in-progress state while the backend worker runs.

## Repository audit

The current frontend uses React 19, TypeScript, TanStack Query, Vitest, React Testing Library, and the shared `apiRequest()` gateway. Feature code follows `api/`, `hooks/`, `components/`, and `__tests__/` boundaries.

Chapter 10 is already integrated into `main`, and `TripDetailPage` is the established trip sub-domain surface. The existing trip detail page already renders itinerary, budget, and recommendation panels.

## Backend contract verified

The current Django configuration mounts the AI Agents application at `/api/ai_agents/`. The actual routes are:

- `POST /api/ai_agents/trips/<uuid:trip_id>/plan/`
- `GET /api/ai_agents/trips/<uuid:trip_id>/plan/status/`

Both endpoints require authentication and the backend resolves the trip against the authenticated user.

The trigger returns HTTP 202 with:

- `message`
- `task_id`
- `trip_id`

The status endpoint returns HTTP 404 when no planning run exists. Once a run exists, it returns the read-only `AgentRunStatusSerializer` fields:

- `id`
- `agent_type`
- `status`
- `error_message`
- `started_at`
- `completed_at`

The backend lifecycle states are `pending`, `running`, `succeeded`, `failed`, and `needs_review`.

The backend also rate-limits planning triggers to five requests per hour and can return HTTP 429. The frontend therefore relies on the shared API client's existing 429 handling instead of implementing a second rate-limit system.

## Reconciliation decisions

### No backend changes

The backend already provides the exact trigger and status endpoints required by this frontend chapter. No backend modification is necessary or justified.

### No arbitrary polling loop

Polling is implemented through TanStack Query's `refetchInterval`, but only while the backend status is non-terminal. Terminal statuses stop polling. A missing run (404) is treated as the initial not-started state rather than as an application error.

After a successful trigger, the frontend temporarily continues polling even if the worker has not created its `AgentRun` yet. This accounts for the real asynchronous boundary between HTTP 202 queueing and worker-side `AgentRun` creation without inventing a client-side run identifier.

### No client-side AgentRun state machine

The backend owns lifecycle state. The frontend displays the authoritative status and only uses the known terminal-state set to decide whether polling should continue.

### Chapter 12 boundary

This chapter provides the trigger and basic polling/progress representation required to make asynchronous planning usable. It does not attempt to implement the more detailed Agent Run status/live-progress experience assigned to Chapter 12.

### Existing architecture preserved

The feature uses:

`TripDetailPage → feature hook → feature API → apiRequest → backend`

No direct `fetch()`, Axios, new dependency, new route, or authentication implementation is introduced.

On successful completion, the existing trip, itinerary, budget, and recommendations query keys are invalidated so the current trip-detail panels can display authoritative AI-generated data. No new cache abstraction is introduced.

## Implementation shape

```text
frontend/src/features/ai-planner/
├── api/
│   └── aiPlannerApi.ts
├── hooks/
│   ├── useTripPlanStatus.ts
│   └── useTriggerTripPlan.ts
├── components/
│   └── TripAIPlannerPanel.tsx
└── __tests__/
    ├── aiPlannerApi.test.ts
    └── TripAIPlannerPanel.test.tsx
```

The panel is mounted on the existing trip detail page immediately before the itinerary/budget/recommendation sub-domain panels so the user can start planning from the trip context without inventing a new route.

## Safety boundary

- Backend files changed: **No**
- New dependencies: **No**
- New routes: **No**
- Authentication changes: **No**
- AI generation logic: **No**
- Arbitrary retry loop: **No**

## Verification limitation

Repository changes are published through GitHub. The execution environment available to this implementation cannot reach `github.com` from a local shell, so local `npm run test` and `npm run build` cannot be honestly claimed as locally executed. GitHub Actions is the authoritative CI verification for the published commit/PR.
