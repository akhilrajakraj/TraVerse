# Chapter 11 — AI Planner `needs_review` Error Reconciliation

## Reported production behavior

The Chapter 11 frontend correctly reached the backend-controlled `needs_review` state. The returned error was:

> Unable to produce valid structured output. Initial error: Unterminated string starting at: line 308 column 23 (char 9659); Repair error: Expecting property name enclosed in double quotes: line 308 column 31 (char 9652)

## Root cause

This is not a React rendering or polling failure. The frontend only receives the persisted `AgentRun.error_message`; it does not receive or generate the malformed LLM JSON.

The AI provider client was calling the chat completion endpoint without a JSON response mode. The planner prompt requested JSON, but that was only an instruction. The configured default model (`llama-3.1-8b-instant`) supports Groq JSON Object Mode, but the client was not enabling it. Therefore a malformed JSON string could reach `json.loads()`.

The structured-output repair path also supplied the original malformed response but did not explicitly include the Pydantic schema in the repair prompt. This made the repair attempt weaker than it should be.

The error therefore occurs before frontend rendering:

`LLM response → json.loads() → repair attempt → repair json.loads() → StructuredOutputInvalid → AgentRun.needs_review`

## Reconciliation decision

A frontend-only fix cannot make an invalid server-side LLM response become valid because the frontend receives only the final `AgentRunStatusSerializer` result. It can improve recovery UX, but it cannot repair the lost raw model output.

Therefore the minimum safe backend correction is:

1. Enable Groq `response_format={"type": "json_object"}` for normal structured AI calls.
2. Preserve the existing model, provider abstraction, retry policy, and agent interfaces.
3. Include the actual Pydantic JSON schema in the repair prompt.
4. Preserve the existing single repair attempt and `StructuredOutputInvalid` contract.

No Django view, URL, model, Celery task, persistence workflow, authentication flow, or database behavior is changed.

## Frontend hardening

The Chapter 11 panel is additionally improved to:

- present `needs_review` as a recoverable AI-output problem rather than a generic application failure;
- explain that no generated trip data should be treated as complete;
- provide a direct retry action;
- keep the technical parser error available as diagnostic detail without making it the primary message;
- preserve backend-controlled lifecycle state and existing query invalidation behavior.

## Verification boundary

The backend correction is intentionally limited to the shared AI client/parser because the defect is upstream of the REST API. The frontend remains the primary UX surface. Tests cover JSON-mode request construction and schema-aware repair prompting in addition to the existing parser behavior.
