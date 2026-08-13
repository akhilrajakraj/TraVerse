# Chapter 11 — AI Planner Structured-Output Recovery

## Incident

After Chapter 11 was merged and pulled, the AI Planner reached the backend-controlled `needs_review` state with:

`Unterminated string starting at: line 308 column 23 ... Repair error: Expecting property name enclosed in double quotes ...`

## Diagnosis

The React frontend was not producing this error. It only rendered `AgentRun.error_message` returned by the status API.

The failure path was:

`Groq response → json.loads() → repair response → json.loads() → StructuredOutputInvalid → AgentRun.needs_review`

The provider client was not requesting JSON Object Mode for structured calls, so the model could return malformed JSON even though the prompt required JSON. The repair prompt also lacked the exact Pydantic schema.

Groq documents JSON Object Mode through `response_format={"type":"json_object"}` and lists `llama-3.1-8b-instant` as supporting JSON Object Mode. The current fix uses that compatible mode rather than changing the application's configured model.

## Fix

### Backend — necessary, narrowly scoped

- Added optional JSON Object Mode to the shared Groq client.
- Structured Travel Planner, Budget, Weather, Recommendation, and Packing calls explicitly enable JSON mode.
- Weather tool-selection remains a normal tool call; only its final response uses JSON mode.
- Conversational `ChatAgent` behavior remains unchanged because JSON mode defaults to `False`.
- Structured-output repair now embeds the exact Pydantic JSON schema and explicitly requests one valid JSON object.
- Existing retry, validation, `StructuredOutputInvalid`, AgentRun lifecycle, Celery workflow, API URLs, authentication, and persistence behavior remain unchanged.

### Frontend — recovery UX

- `needs_review` is now described as an AI-output recovery state rather than a generic application failure.
- The raw parser diagnostic is behind a technical-details disclosure.
- The UI explicitly tells the user that the failed run is not considered a completed plan.
- Terminal planner states expose `Retry AI planner`.
- Existing backend-controlled polling and successful-query invalidation remain intact.

## Tests added/updated

- Groq client JSON-mode request coverage.
- Conversation calls do not accidentally enable JSON mode.
- Schema-aware repair prompt coverage.
- `needs_review` frontend recovery coverage.

## Safety boundary

No Django views, URLs, models, migrations, Celery tasks, database writes, authentication, or external frontend dependencies were changed.
