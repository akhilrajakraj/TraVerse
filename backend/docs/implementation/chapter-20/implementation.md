Chapter 20 — documents / RAG Development — Implementation

Volume 5: Conversational Layer | Chapter 20 of 29

1. Implementation Scope

The current repository implements destination retrieval across these boundaries:

backend/apps/destinations/selectors.py
backend/apps/ai_agents/destination_search.py
backend/ai/tools/destination_search.py
backend/ai/agents/chat_agent.py
backend/ai/prompts/chat_agent_v1.py
backend/apps/ai_agents/services.py
backend/apps/destinations/tests/test_selectors.py
backend/ai/tests/test_chat_agent.py
backend/apps/ai_agents/tests/test_services.py

The original chapter's file list used destination_search_tool.py and a Django-aware executor inside apps/ai_agents/services.py; the current repository has evolved to a separate typed tool-result module and a dedicated AI-agent retrieval adapter. fileciteturn160file0L70-L92

2. Selector Layer

apps/destinations/selectors.py

The selector is the database-facing retrieval boundary.

Its responsibility is:

user/search query
        ↓
Django ORM query
        ↓
active destinations
        ↓
ordered QuerySet

The current selector:

strips the query,

returns no results for an empty query,

filters is_active=True,

searches name,

searches country,

searches city,

searches summary,

searches description,

searches tags,

orders by country, city, and name. fileciteturn152file0L2-L2

Current implementation

def search_destinations(*, query: str) -> QuerySet[Destination]:
    query = query.strip()

    if not query:
        return Destination.objects.none()

    return (
        Destination.objects.filter(
            is_active=True,
        )
        .filter(
            Q(name__icontains=query)
            | Q(country__icontains=query)
            | Q(city__icontains=query)
            | Q(summary__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
        )
        .order_by(
            "country",
            "city",
            "name",
        )
    )

3. Why Selector Extraction Matters

The original Chapter 20 extracted the destination query from DestinationListCreateView.

The reason was the appearance of a genuine second consumer: RAG.

This follows the project's "rule of two":

One consumer
    ↓
keep logic local

Second genuine consumer
    ↓
extract shared logic

The original chapter explicitly identifies this as the point at which abstraction became justified. fileciteturn160file0L52-L54

The current selector now documents itself as reusable by:

API views,

AI retrieval,

future recommendation engines. fileciteturn152file0L2-L2

4. Retrieval Result Boundary

ai/tools/destination_search.py

The current repository does not pass Django Destination ORM objects directly into the AI agent.

Instead it defines:

@dataclass(frozen=True)
class DestinationSearchResult:
    name: str
    country: str
    city: str
    latitude: Decimal
    longitude: Decimal
    summary: str
    description: str
    tags: list[str]

This is an important boundary.

Django ORM object
        ↓
AI-safe data object
        ↓
Chat Agent

The tool module explicitly states that it does not access the Django ORM directly. fileciteturn153file0L2-L2

5. Retrieval Adapter

apps/ai_agents/destination_search.py

This module bridges:

Django selector
        ↓
AI-safe result

Its responsibility is deliberately small.

for destination in search_destinations(query=query):
    results.append(
        DestinationSearchResult(
            name=destination.name,
            country=destination.country,
            city=destination.city,
            latitude=destination.latitude,
            longitude=destination.longitude,
            summary=destination.summary,
            description=destination.description,
            tags=destination.tags,
        )
    )

The current adapter therefore prevents the AI package from needing to understand Django ORM models. fileciteturn154file0L2-L2

6. Chat Agent Integration

ai/agents/chat_agent.py

The current ChatAgent.reply() accepts:

conversation_context
user_message
retrieved_destinations

The retrieved list defaults to empty:

retrieved_destinations or []

and is forwarded to the prompt renderer. fileciteturn155file0L2-L2

This means existing callers can continue to call:

agent.reply(
    conversation_context=...,
    user_message=...,
)

without having to manufacture retrieval data.

7. Prompt Integration

ai/prompts/chat_agent_v1.py

The prompt layer remains independent of:

Django,

database queries,

ORM models,

Groq-specific retrieval logic.

It receives already-prepared destination objects.

When results exist, it constructs:

Retrieved Destinations:
- Name, City, Country
  Summary: ...
  Description: ...
  Tags: ...

before the latest user message. fileciteturn156file0L2-L2

This keeps retrieval mechanics outside the prompt layer.

8. Chat Service Integration

apps/ai_agents/services.py

The current conversational workflow is:

Get/create active session
        ↓
Persist user message
        ↓
Build memory
        ↓
Optimize memory
        ↓
Build transcript
        ↓
search_destination(user_message)
        ↓
ChatAgent.reply(...)
        ↓
Persist assistant response
        ↓
Return response

The current implementation explicitly performs:

retrieved_destinations = search_destination(
    query=user_message,
)

and passes the result into:

agent.reply(
    conversation_context=conversation_context,
    user_message=user_message,
    retrieved_destinations=retrieved_destinations,
)

fileciteturn158file0L2-L2

9. Travel Planner Integration

RAG is also attached to the travel-planner state.

The current service:

initial_state = _attach_destination_context(
    state=initial_state,
    user_message=" ".join(
        initial_state["destination_names"],
    ),
)

The retrieved objects are then converted into serializable dictionaries for the AgentRun.input_snapshot, including conversion of Decimal coordinates to floats. fileciteturn158file0L2-L2

This is a current-repository evolution beyond the original Chapter 20 document.

10. Why the Current Result Object Is Important

The current RAG boundary can be visualized as:

apps.destinations
        │
        │ Django ORM
        ▼
search_destinations()
        │
        │ Destination model
        ▼
apps.ai_agents.destination_search
        │
        │ conversion
        ▼
DestinationSearchResult
        │
        │ plain structured data
        ▼
ai.agents.ChatAgent

The AI layer therefore receives data, not Django behavior.

11. No Vector Database

There is no model, migration, vector store, embedding pipeline, or semantic-search dependency introduced for this chapter.

The retrieval mechanism is ordinary structured database search.

This is intentional, not an unfinished implementation.

The original chapter explicitly rejects a vector database because the catalog is structured and small. fileciteturn160file0L34-L40

12. Current Search Fields

The current selector searches:

name
country
city
summary
description
tags

The original chapter initially discussed:

name
country
description

and explicitly justified expanding description matching for travel questions. fileciteturn160file0L155-L168

The current repository has evolved further by incorporating additional structured knowledge fields.

13. Blank Query Behavior

The current selector deliberately refuses to return the entire catalog for an empty query.

if not query:
    return Destination.objects.none()

This behavior is directly tested. fileciteturn162file0L2-L2

This prevents accidental broad retrieval.

14. Inactive Destination Protection

The selector always begins with:

Destination.objects.filter(
    is_active=True,
)

Therefore deactivated destinations cannot become RAG context.

The current tests explicitly verify this behavior. fileciteturn162file0L2-L2

15. Testing Architecture

The current repository divides responsibility across:

apps/destinations/tests/test_selectors.py
        ↓
selector correctness

ai/tests/test_chat_agent.py
        ↓
prompt/result forwarding

apps/ai_agents/tests/test_services.py
        ↓
Django → AI service integration

The chat-agent tests verify that retrieved destination objects are forwarded to the prompt. fileciteturn163file0L2-L2

16. Current vs Original Chapter 20

Area

Original Chapter 20

Current repository

Retrieval

Tool-calling RAG

Direct retrieval adapter

Tool schema

destination_search_tool.py

destination_search.py dataclass

Executor

_search_destinations_executor

search_destination() adapter

LLM decision

LLM decides whether to call tool

Service retrieves on chat message

ORM boundary

Executor in apps.ai_agents.services

Selector + adapter

Result type

JSON string

DestinationSearchResult

Search fields

name/country/description

name/country/city/summary/description/tags

RAG context

Tool response

Explicit prompt context

Vector DB

No

No

The original source is preserved as historical architecture; the table above describes the current implementation observed in the repository.

17. Important Documentation Rule

Do not copy the old Chapter 20 code into the current project without reconciliation.

For example, the old chapter refers to:

ai/tools/destination_search_tool.py
GroqClient.call_with_tools()
_search_destinations_executor()

while the current repository exposes:

ai/tools/destination_search.py
apps/ai_agents/destination_search.py
ChatAgent.reply(retrieved_destinations=...)

The current source must win when describing the current implementation. fileciteturn153file0L2-L2 fileciteturn154file0L2-L2 fileciteturn155file0L2-L2