# Frontend Chapter 11 — AI Planner Trigger, Polling & Structured-Output Reconciliation

## Original chapter intent

Implement the frontend entry point for asynchronous AI trip planning and represent the planner's in-progress state while the backend worker runs.

## Repository audit

The frontend uses React 19, TypeScript, TanStack Query, Vitest, React Testing Library, and the shared `apiRequest()` gateway. Feature code follows `api/`, `hooks/`, `components/`, and `__tests__/` boundaries.

Chapter 10 is already integrated into `main`, and `TripDetailPage` is the established trip sub-domain surface.

## Backend contract verified

The actual routes are:

- `POST /api/ai_agents/trips/<uuid:trip_id>/plan/`
- `GET /api/ai_agents/trips/<uuid:trip_id>/plan/status/`

The trigger returns HTTP 202 with `message`, `task_id`, and `trip_id`. The status endpoint returns HTTP 404 when no planning run exists and otherwise exposes `id`, `agent_type`, `status`, `error_message`, `started_at`, and `completed_at`.

The backend lifecycle states are `pending`, `running`, `succeeded`, `failed`, and `needs_review`.

## Reported failure and reconciliation

After Chapter 11 was pulled into a real environment, the UI correctly surfaced `needs_review` with:

`Unterminated string starting at: line 308 column 23 ... Repair error: Expecting property name enclosed in double quotes ...`

This error originates inside the AI workflow, not inside React. The frontend receives the persisted `AgentRun.error_message`; it cannot repair an LLM response that has already failed server-side JSON parsing.

The audit found two reliability gaps upstream:

1. The Groq client requested ordinary text completion even when agents expected structured JSON. The planner prompt said JSON, but the provider was not instructed through `response_format` to enforce JSON syntax.
2. The generic repair prompt included the malformed response but not the exact Pydantic schema, so the repair model had weaker structural guidance.

The minimal backend correction is therefore limited to the AI infrastructure boundary:

- structured calls can enable Groq JSON Object Mode;
- tool-selection calls remain ordinary tool calls, while their final response can use JSON mode;
- structured agents explicitly request JSON mode;
- repair prompts include the exact Pydantic JSON schema.

No Django view, URL, model, Celery task, persistence workflow, authentication flow, or database behavior is changed.

Groq documents that `llama-3.1-8b-instant` supports JSON Object Mode, and its API accepts `response_format: {"type": "json_object"}` for valid JSON generation. Groq also documents stricter JSON Schema Structured Outputs for a limited model set; the current TraVerse default model is therefore kept and JSON Object Mode is used as the compatible minimal fix.

## Frontend recovery hardening

The frontend remains responsible for the user experience:

- `needs_review` is presented as a recoverable AI-output problem;
- the raw parser diagnostic is moved behind a technical-details disclosure;
- the UI explicitly says that the failed run is not treated as a completed plan;
- the terminal state exposes `Retry AI planner`;
- active runs continue backend-controlled polling;
- successful runs invalidate the existing trip, itinerary, budget, and recommendation caches;
- no client-side AgentRun state machine or AI generation logic is introduced.

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

## Safety boundary

- Frontend changes: **Yes — recovery UX and regression coverage**
- Backend changes: **Yes — only the shared AI client/parser and structured-agent call flags because the root defect is server-side**
- Django API/view changes: **No**
- Database/model changes: **No**
- Celery/task changes: **No**
- New dependencies: **No**
- New routes: **No**
- Authentication changes: **No**
- Arbitrary infinite polling: **No**

## Verification limitation

The repository changes are published through GitHub. Local `npm run test`, `npm run build`, and backend pytest execution have not been claimed because the available shell cannot reach GitHub/network services. CI is the authoritative verification path.
