# Chapter 11 — AI Planner Structured-Output Recovery

## Incident

After Chapter 11 was pulled into a real environment, the AI Planner reached the backend-controlled `needs_review` state with:

`Unterminated string starting at: line 308 column 23 ... Repair error: Expecting property name enclosed in double quotes ...`

## Diagnosis

This is not a React rendering or polling error. The frontend receives the persisted `AgentRun.error_message`; the malformed JSON is produced inside the AI workflow before the frontend sees it.

The failure path is:

`LLM response → json.loads() → repair response → json.loads() → StructuredOutputInvalid → AgentRun.needs_review`

The shared Groq client previously requested ordinary model output even for structured agents. The prompts requested JSON, but the provider was not asked to enforce JSON syntax. The repair prompt also did not contain the exact Pydantic schema.

Groq documents that `llama-3.1-8b-instant` supports JSON Object Mode and that `response_format={"type":"json_object"}` ensures valid JSON syntax. Groq also documents stricter JSON Schema Structured Outputs for a limited model set; TraVerse keeps its current model and uses JSON Object Mode as the compatible minimal fix.

## Backend change — necessary and narrowly scoped

- The shared Groq client now supports JSON Object Mode and enables it by default for AI calls.
- `ChatAgent` explicitly opts out so conversational replies remain ordinary text.
- Tool-selection requests remain normal tool calls; the final tool result can use JSON mode.
- The structured-output repair prompt now includes the exact Pydantic JSON schema.
- Existing Django APIs, URLs, AgentRun lifecycle, Celery tasks, persistence, authentication, and database behavior remain unchanged.

## Frontend hardening

The Chapter 11 planner panel now:

- explains `needs_review` as an AI-output recovery state;
- clearly says the failed run is not considered a completed plan;
- hides the raw parser diagnostic behind technical details;
- exposes `Retry AI planner` for terminal failures;
- preserves backend-controlled polling and successful cache invalidation.

## Tests

Added coverage for:

- provider JSON mode;
- disabling JSON mode for conversational calls;
- schema-aware repair prompts;
- `needs_review` recovery UX.

## Safety boundary

No new dependency, API route, Django view, model, migration, Celery task, authentication change, or database workflow was introduced.
