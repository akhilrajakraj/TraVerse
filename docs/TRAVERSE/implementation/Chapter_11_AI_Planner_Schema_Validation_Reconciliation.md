# Chapter 11 — AI Planner Schema-Validation Reconciliation

## Incident

After the Chapter 11 structured-output recovery fix, the planner stopped failing on malformed JSON syntax but still reached `needs_review` with a Pydantic validation error:

- Initial response: `ItineraryPlanSchema.days` was missing because the model returned a different object shape containing fields such as `tripTitle`.
- Repair response: the model returned a list containing JSON Schema metadata such as `$defs`, rather than an itinerary instance.

## Root cause

Groq JSON Object Mode guarantees JSON syntax, not application-schema adherence. Groq's documentation explicitly distinguishes JSON Object Mode from Structured Outputs: JSON Object Mode can return valid JSON that does not match the intended schema. citeturn0search0turn0search1

The existing `ItineraryPlanSchema` correctly requires a top-level `days` list. The model prompt previously said to follow the schema but did not show the actual instance shape. The repair prompt showed the JSON Schema definition but did not strongly distinguish the schema definition from the JSON instance that must be returned.

## Safe fix

The fix is intentionally confined to the AI generation boundary:

1. Keep the existing Groq model, client abstraction, JSON Object Mode, parser, Pydantic schema, agent, graph, Celery task, and persistence workflow.
2. Strengthen the Travel Planner system prompt with the exact expected JSON object shape and a representative instance.
3. Explicitly forbid unsupported top-level fields such as `tripTitle` and schema metadata such as `$defs`.
4. Strengthen the repair prompt to state that the schema is a definition, not the answer, and require exactly one JSON object instance.
5. Add regression tests for the prompt contract and schema-document repair failure.

## Deliberate non-changes

- No Django API changes.
- No URL changes.
- No model or migration changes.
- No AgentRun lifecycle changes.
- No Celery task changes.
- No authentication changes.
- No database changes.
- No model/provider switch.
- No new dependency.
- No frontend architecture change.

The existing Chapter 11 frontend remains responsible for displaying the authoritative `AgentRun` state and providing retry UX; it does not attempt to manufacture or repair server-side AI data.
