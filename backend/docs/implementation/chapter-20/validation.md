Chapter 20 — RAG Development — Validation

Volume 5: Conversational Layer | Chapter 20 of 29

1. Validation Objective

Validation must prove that:

Destination data
        ↓
structured retrieval
        ↓
AI-safe transformation
        ↓
prompt augmentation
        ↓
chat generation

works without weakening existing destination-search behavior.

The original chapter explicitly designed tests around:

selector extraction,

regression of the existing destination API,

ChatAgent tool behavior,

executor behavior,

generate_chat_reply() wiring. fileciteturn160file0L355-L490

The current repository has evolved the implementation, so current validation is centered on the current selector/result-object/chat-agent architecture.

2. Selector Validation

Current selector tests verify:

Blank query

A blank query returns zero results.

fileciteturn162file0L2-L2

Name search

A destination name can be retrieved.

Country search

A country can be retrieved.

City search

A city can be retrieved.

Inactive destination exclusion

Inactive destinations are not returned.

Knowledge fields

Summary, description, and tags remain available in retrieved objects.

Knowledge-field search

A query such as a tag/knowledge term can retrieve the destination.

These behaviors are explicitly represented in the current test suite. fileciteturn162file0L2-L2

3. Retrieval Result Validation

The current DestinationSearchResult is a frozen dataclass.

Validation should establish that retrieval produces:

name
country
city
latitude
longitude
summary
description
tags

rather than leaking the Django model into the AI layer.

The result contract is defined in ai/tools/destination_search.py. fileciteturn153file0L2-L2

4. Adapter Validation

The retrieval adapter:

apps.ai_agents.destination_search.search_destination()

must:

call the shared selector,

iterate through matching destinations,

create DestinationSearchResult objects,

return a list,

return an empty list when no results exist.

The current implementation performs exactly this transformation. fileciteturn154file0L2-L2

5. ChatAgent Validation

Current tests verify:

Default retrieval state

Calling:

agent.reply(
    conversation_context="Conversation",
    user_message="Hello",
)

causes the prompt to receive:

retrieved_destinations=[]

Explicit retrieval

When destinations are supplied, the exact collection is forwarded to the prompt.

Existing LLM call behavior

The ChatAgent still calls the configured Groq client.

Temperature

The current test suite expects:

temperature = 0.3

Response normalization

The response is stripped before returning.

fileciteturn163file0L2-L2

6. Prompt Validation

The prompt layer must:

preserve conversation context
+
include retrieved destinations when present
+
include latest user message

The current prompt formats retrieved destinations using:

name
city
country
summary
description
tags

fileciteturn156file0L2-L2

7. Chat-Service Validation

The current generate_chat_reply() workflow should be validated as:

user message
    ↓
persist user message
    ↓
build memory
    ↓
optimize memory
    ↓
build transcript
    ↓
search destination
    ↓
ChatAgent
    ↓
persist assistant message

The current implementation contains the retrieval call immediately before ChatAgent execution. fileciteturn158file0L2-L2

8. Travel-Planner Validation

The current repository also attaches destination context during travel-planner execution.

Validation should confirm:

destination names
        ↓
search_destination()
        ↓
retrieved_destinations
        ↓
AgentRun.input_snapshot

The service serializes the retrieved dataclass values and converts coordinates before storing them in the snapshot. fileciteturn158file0L2-L2

9. No-Migration Validation

The original Chapter 20 explicitly states:

No migrations this chapter — no model changes.

fileciteturn160file0L102-L109

The current RAG implementation also introduces no new database model.

The selector operates against the existing Destination model.

10. Regression Validation

A critical requirement is that adding RAG must not break the normal destination API.

The original chapter specifically required a regression test proving that the Chapter 6 search behavior survived selector extraction. fileciteturn160file0L390-L403

The current repository retains dedicated selector tests, so this behavior remains part of the validation boundary. fileciteturn162file0L2-L2

11. Security/Data Validation

The retrieval system must never expose inactive destinations.

This is enforced at the selector layer:

is_active=True

fileciteturn152file0L2-L2

The selector tests explicitly verify inactive destinations are excluded. fileciteturn162file0L2-L2

12. Architecture Validation

The following boundary must remain true:

ai/
    NO Django ORM

apps/destinations/
    owns database search

apps/ai_agents/
    bridges Django data to AI-safe structures

The current source confirms that ai/tools/destination_search.py contains a pure dataclass definition rather than ORM access. fileciteturn153file0L2-L2

13. Test Commands

The original Chapter 20 documented:

docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.destinations apps.ai_agents -v 2

fileciteturn160file0L102-L109

For the current implementation, the same broad areas remain the relevant test targets:

docker compose exec web pytest ai/tests -v
docker compose exec web python manage.py test apps.destinations apps.ai_agents -v 2

14. Validation Matrix

Layer

What must be true

Selector

Correct structured destinations returned

Selector

Blank query returns nothing

Selector

Inactive destinations excluded

Selector

Knowledge fields searchable

Adapter

ORM objects converted to AI-safe results

Result contract

Required destination fields preserved

ChatAgent

Retrieved results forwarded

Prompt

Retrieved context rendered

Chat service

Retrieval connected to conversation flow

Planner

Retrieval snapshot serialized correctly

AI boundary

No Django imports inside pure ai/ tool definition

Regression

Existing destination behavior remains intact

Migration

No new migration required

15. Current vs Original Validation

The original Chapter 20 tests were designed around:

call_with_tools()
_search_destinations_executor()
tool schema
LLM tool-calling

The current repository tests are instead centered around:

search_destinations()
DestinationSearchResult
search_destination()
ChatAgent.reply(retrieved_destinations=...)

The validation strategy therefore follows the current implementation rather than asserting behavior that no longer exists in the source.

16. Runtime Test Result Boundary

The repository evidence reviewed for this documentation establishes the test structure and assertions.

It does not, from the source files alone, constitute a fresh runtime execution of every current test command.

Therefore this documentation does not invent a new test count or claim a fresh all-green run unless one is actually executed.

A fresh runtime test run remains the final release gate.

17. Acceptance Checklist

RAG retrieves from the project's own destination catalog.

Vector database is deliberately not required.

Search logic is reusable through apps.destinations.selectors.

Blank queries return no destinations.

Inactive destinations are excluded.

Name/country/city/knowledge fields are searchable.

AI receives typed DestinationSearchResult objects.

AI-facing retrieval code does not directly use Django ORM.

ChatAgent accepts retrieved destination context.

Prompt renders retrieved destination context.

Chat continues when retrieval returns no results.

Travel-planner state can carry retrieved destination context.

Retrieval context can be serialized into AgentRun.input_snapshot.

Current selector tests cover core retrieval behavior.

Current ChatAgent tests cover retrieved-context forwarding.

A fresh runtime execution of all relevant test commands has been performed for this documentation release.

A Git commit for this documentation release has been performed.

18. Final Acceptance Principle

Chapter 20 should be considered technically healthy when the system can demonstrate:

real catalog data
      ↓
real retrieval
      ↓
structured AI context
      ↓
real conversational prompt
      ↓
grounded generation

while retaining:

no unnecessary vector database
no Django dependency inside the pure AI package
no exposure of inactive catalog data
no regression of normal destination search