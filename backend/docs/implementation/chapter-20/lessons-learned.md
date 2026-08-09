Chapter 20 — RAG Development — Lessons Learned

Volume 5: Conversational Layer | Chapter 20 of 29

1. RAG Is Not Synonymous With Vector Search

The first lesson is the most important.

RAG means:

retrieve → augment → generate

It does not inherently mean:

embeddings → vector database → similarity search

The original Chapter 20 deliberately rejected vector infrastructure because TraVerse's destination catalog is structured and searchable through ordinary database queries. fileciteturn160file0L30-L40

2. Choose Retrieval Technology From the Data Shape

TraVerse's catalog has known fields.

Therefore:

structured data
        ↓
structured query

is a better match than:

structured data
        ↓
embedding everything
        ↓
vector similarity

The lesson is not "never use vectors."

The lesson is:

Use semantic retrieval when the problem actually requires semantic retrieval.

3. The Second Consumer Justifies the Selector

Chapter 6 had search logic inside a view.

At that time there was only one consumer.

Chapter 20 introduced another consumer.

Therefore:

one consumer
    ↓
local logic

second consumer
    ↓
shared selector

The original chapter explicitly calls this the "rule of two." fileciteturn160file0L52-L54

This is a general refactoring lesson.

4. Keep Django Out of the AI Package

The AI package should not know:

Django ORM
Django models
QuerySets
request.user

The current architecture preserves this separation.

Django
  ↓
selector
  ↓
AI-safe result object
  ↓
AI package

The current DestinationSearchResult is explicitly defined without Django imports. fileciteturn153file0L2-L2

5. Structured Result Objects Are Better Than Passing ORM Models

Passing a Django model directly into the AI layer creates hidden coupling.

The current system instead converts:

Destination

into:

DestinationSearchResult

with only the fields the AI needs.

That gives the AI layer a stable contract.

6. Retrieval Should Be Explicit Context

The current prompt receives:

Retrieved Destinations

as structured contextual information.

The prompt itself does not execute database queries.

This preserves the division:

retrieval layer
    retrieves

prompt layer
    formats

LLM
    reasons

The current prompt implementation follows this boundary. fileciteturn156file0L2-L2

7. Empty Retrieval Is a Valid State

A retrieval system should not assume that every query produces results.

The current adapter returns:

[]

when nothing matches.

The ChatAgent then receives an empty retrieval collection.

This allows the conversational system to continue naturally rather than failing simply because the catalog has no match.

8. Inactive Data Must Never Become Context

The selector's:

is_active=True

filter is a domain rule, not just an optimization.

If an administrator deactivates a destination, the AI should not continue treating it as valid catalog knowledge.

The current selector and tests preserve this invariant. fileciteturn152file0L2-L2 fileciteturn162file0L2-L2

9. Blank Retrieval Queries Need Defensive Behavior

A blank query could accidentally mean:

return every destination

The current selector explicitly avoids this.

blank query
    ↓
empty QuerySet

The test suite verifies that behavior. fileciteturn162file0L2-L2

10. RAG Context Is a Data Contract

The current DestinationSearchResult provides a contract:

name
country
city
latitude
longitude
summary
description
tags

This is preferable to passing an arbitrary dictionary whose shape can change silently.

A typed result object makes the retrieval boundary explicit.

11. Retrieval and Generation Are Different Responsibilities

The system separates:

retrieval
    ↓
search_destination()

generation
    ↓
ChatAgent.reply()

This matters because the retrieval layer can be tested without invoking the LLM.

It also means a future retrieval implementation can change without requiring the entire conversational agent to be rewritten.

12. Test RAG Without Depending on the LLM

A strong RAG test strategy isolates:

Retrieval

Does the selector return the correct destination?

Transformation

Does the adapter create the correct DestinationSearchResult?

Prompt integration

Does the ChatAgent receive retrieved destinations?

Full service

Does generate_chat_reply() retrieve context and pass it into the agent?

This is far more reliable than using a live LLM response as the only proof that RAG works.

The current ChatAgent tests already verify retrieval objects reach the prompt. fileciteturn163file0L2-L2

13. Current Architecture Demonstrates Evolution, Not Failure

The original chapter proposed LLM tool-calling.

The current repository uses direct retrieval before the ChatAgent.

That should not automatically be interpreted as the original architecture "failing."

The underlying goal remains:

catalog data
    ↓
retrieval
    ↓
AI context
    ↓
generation

The implementation boundary evolved toward a simpler typed adapter.

14. Simplicity Is an Architectural Feature

The current implementation does not introduce:

vector databases,

embedding models,

indexing pipelines,

background embedding jobs,

synchronization workers,

additional external services.

That dramatically reduces:

deployment complexity
operational complexity
data synchronization problems
testing complexity
cost

For this data shape, that simplicity is a deliberate architectural advantage.

15. Reuse Existing Infrastructure Before Creating New Infrastructure

The original Chapter 20 wanted to reuse Chapter 14's tool-calling machinery.

The current implementation goes even further by reusing:

Destination selector
ChatAgent
Chat prompt
Existing conversation memory
Existing AI service boundary

This is consistent with the project's broader engineering style:

Extend existing seams before inventing parallel systems.

16. Search Quality Is a Domain Decision

The current selector searches:

name
country
city
summary
description
tags

That means RAG quality is partly determined by how well the destination catalog itself is populated.

A sophisticated LLM cannot retrieve information that the selector cannot find.

Therefore:

better catalog data
        +
better retrieval
        +
better prompt context
        =
better grounded answers

17. RAG Does Not Eliminate Hallucination by Itself

Retrieval gives the model evidence.

It does not guarantee that the model will always use that evidence correctly.

The current prompt still instructs the model:

Never invent information.
If information is unavailable, say so clearly.

This is a complementary control to retrieval. fileciteturn156file0L2-L2

18. The Retrieval Boundary Should Be Replaceable

The current architecture makes this possible:

search_destinations()
        ↓
DestinationSearchResult

could eventually be replaced by:

semantic_search()
        ↓
DestinationSearchResult

without requiring the ChatAgent to know whether the data came from:

PostgreSQL,

a search index,

an embedding store,

an external retrieval service.

The AI-facing contract remains stable.

19. The Best Future Vector-DB Decision Is Delayed Until Needed

A vector database becomes more justified if TraVerse later introduces:

large unstructured travel documents,

hotel descriptions,

travel guides,

user-generated long-form content,

semantic similarity requirements,

multilingual semantic retrieval,

very large knowledge collections.

Those conditions are different from the current structured destination catalog.

Therefore the current choice is:

No vector database now.
Keep the retrieval boundary replaceable.

20. Chapter 20's Deepest Lesson

The deepest lesson is:

Good AI architecture begins with understanding the data and system boundaries, not with selecting the most sophisticated AI technology.

For TraVerse:

small structured catalog
        ↓
database search
        ↓
typed retrieval result
        ↓
prompt augmentation
        ↓
LLM generation

That is RAG.

It is intentionally simple.