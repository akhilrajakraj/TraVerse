Chapter 20 — Retrieval-Augmented Generation (RAG)

Volume 5: Conversational Layer | Chapter 20 of 29

Chapter 20 closes Volume 5 by grounding TraVerse's conversational AI in the project's own destination catalog. The central engineering lesson is not "add a vector database"; it is learning to recognize that RAG can be implemented with the simplest retrieval mechanism that fits the data, while preserving the project's AI/Django dependency boundary.

1. Chapter Purpose

The original Chapter 20 design introduced RAG as a destination-search tool:

User message
     ↓
Chat Agent
     ↓
LLM decides whether catalog retrieval is needed
     ↓
search_destinations
     ↓
Destination catalog
     ↓
Retrieved destination context
     ↓
LLM response

The original architecture deliberately rejected embeddings/vector search because the destination catalog is small and structured. fileciteturn160file0L30-L40

The current repository has since evolved this implementation.

The current code now uses:

User message
     ↓
apps.ai_agents.services
     ↓
search_destination()
     ↓
apps.destinations.selectors.search_destinations()
     ↓
DestinationSearchResult
     ↓
ChatAgent.reply()
     ↓
ChatAgentPromptV1
     ↓
Retrieved Destinations section
     ↓
GroqClient

The current implementation therefore retains the chapter's core RAG principle—retrieval from the project's own structured catalog—but represents retrieved data as typed AI-safe objects and attaches it directly to the chat prompt. fileciteturn154file0L2-L2 fileciteturn155file0L2-L2

2. Learning Objectives

By the end of this chapter, an engineer should be able to:

Explain Retrieval-Augmented Generation without treating vector databases as synonymous with RAG.

Decide whether structured database retrieval or semantic/vector retrieval is appropriate.

Separate Django ORM access from the provider-independent ai/ package.

Extract reusable database search logic when a second real consumer appears.

Represent retrieved domain data as AI-safe structured objects.

Inject retrieved context into a conversational prompt.

Preserve existing chat behavior when retrieval returns no results.

Test retrieval independently from the LLM provider.

Understand the difference between the original Chapter 20 architecture and the current repository implementation.

3. What RAG Means in TraVerse

RAG means:

Retrieve relevant information
        ↓
Augment the model's context
        ↓
Generate the response

For TraVerse:

Destination catalog
        ↓
search_destinations()
        ↓
DestinationSearchResult[]
        ↓
ChatAgent prompt
        ↓
LLM

The model is not required to invent destination information from training knowledge when matching catalog data is available.

4. Why TraVerse Does Not Need a Vector Database Here

The original Chapter 20 explicitly rejects vector search.

The catalog is:

structured,

relational,

comparatively small,

represented by known fields,

already searchable through database filters.

The original chapter therefore chose targeted icontains retrieval rather than embeddings/vector similarity. fileciteturn160file0L34-L40

This remains consistent with the current repository.

The current selector searches:

name
country
city
summary
description
tags

while requiring:

is_active=True

and applying deterministic ordering. fileciteturn152file0L2-L2

5. Current Architecture

                    ┌─────────────────────┐
                    │     User Message    │
                    └──────────┬──────────┘
                               │
                               ▼
                  generate_chat_reply()
                  apps.ai_agents.services
                               │
                               ▼
                    search_destination()
                  apps.ai_agents.destination_search
                               │
                               ▼
                  search_destinations()
                  apps.destinations.selectors
                               │
                               ▼
                    Destination ORM
                               │
                               ▼
                DestinationSearchResult[]
                               │
                               ▼
                       ChatAgent.reply()
                         ai/agents/
                               │
                               ▼
                    ChatAgentPromptV1
                         ai/prompts/
                               │
                               ▼
                  "Retrieved Destinations"
                               │
                               ▼
                        GroqClient

The current apps.ai_agents.services explicitly retrieves destinations and passes them into ChatAgent.reply(). fileciteturn158file0L2-L2

6. Current Repository Evolution

The original Chapter 20 document describes:

ai/tools/destination_search_tool.py
        +
LLM tool-calling
        +
GroqClient.call_with_tools()
        +
_search_destinations_executor()

and says the LLM decides whether retrieval is needed. fileciteturn160file0L44-L54

The current repository instead contains:

ai/tools/destination_search.py
        ↓
DestinationSearchResult

and:

apps/ai_agents/destination_search.py
        ↓
search_destination()

with the service layer calling retrieval directly before invoking ChatAgent. fileciteturn153file0L2-L2 fileciteturn154file0L2-L2

This documentation therefore treats the current repository as authoritative while preserving the original chapter's architectural lessons.

7. Completion Definition

Chapter 20 is complete when:

destination search is reusable outside the HTTP view,

inactive destinations cannot be retrieved,

knowledge fields are searchable,

retrieved data crosses into the AI layer without Django model coupling,

chat prompts can receive retrieved destinations,

normal chat still works without retrieval results,

retrieval is tested independently,

chat-agent integration is tested,

the existing application test suite remains healthy,

and the implementation remains free of unnecessary vector-database infrastructure.

8. Key Engineering Principle

The deepest lesson is:

RAG is an architecture pattern, not a database product.

TraVerse's RAG is deliberately built around the data it actually has rather than around whatever technology is fashionable.