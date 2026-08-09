Chapter 20 — RAG Development — Troubleshooting

Volume 5: Conversational Layer | Chapter 20 of 29

1. No Destinations Are Retrieved

Symptom

search_destination("Japan")

returns an empty list.

Check the selector

docker compose exec web python manage.py shell -c "
from apps.destinations.selectors import search_destinations
print(list(
    search_destinations(query='Japan')
    .values_list('name', flat=True)
))
"

The current selector searches:

name
country
city
summary
description
tags

and only active destinations. fileciteturn152file0L2-L2

2. Blank Query Returns Everything

This must not happen.

The current implementation deliberately returns:

Destination.objects.none()

when the stripped query is empty. fileciteturn152file0L2-L2

The selector test explicitly verifies zero results for a blank query. fileciteturn162file0L2-L2

3. Inactive Destinations Appear in RAG

Cause

The is_active=True condition was removed or bypassed.

Fix

Ensure retrieval goes through:

apps.destinations.selectors.search_destinations()

rather than querying Destination.objects directly.

The current selector enforces the active filter. fileciteturn152file0L2-L2

4. AI Package Starts Importing Django

Symptom

A developer adds:

from apps.destinations.models import Destination

inside:

ai/tools/

or:

ai/agents/

Why this is wrong

The architecture intentionally keeps Django access outside the provider-independent AI package.

The current ai/tools/destination_search.py contains only the result contract and standard-library imports. fileciteturn153file0L2-L2

Fix

Keep:

Django ORM
    ↓
apps/ai_agents
    ↓
DestinationSearchResult
    ↓
ai/

5. ChatAgent Receives a Django Model

Symptom

A Destination ORM object is passed into:

ChatAgent.reply(...)

Fix

Convert it through:

apps.ai_agents.destination_search.search_destination()

which produces DestinationSearchResult objects. fileciteturn154file0L2-L2

6. Retrieved Data Is Not Appearing in the Prompt

Check the chain:

generate_chat_reply()
        ↓
search_destination()
        ↓
ChatAgent.reply()
        ↓
ChatAgentPromptV1.render_user_prompt()

The current service explicitly passes:

retrieved_destinations=retrieved_destinations

to the agent. fileciteturn158file0L2-L2

The ChatAgent forwards the same collection to the prompt renderer. fileciteturn155file0L2-L2

The prompt then creates the:

Retrieved Destinations:

section. fileciteturn156file0L2-L2

7. Prompt Contains No Retrieval Section

If no destination matches the query, this is expected.

The prompt only creates the retrieval section when:

if retrieved_destinations:

is true. fileciteturn156file0L2-L2

8. Search Matches Name but Not Description/Tags

Verify the selector includes all current fields:

name
country
city
summary
description
tags

The current repository tests specifically exercise knowledge-field searching, including a tag query. fileciteturn162file0L2-L2

9. Search Behavior Changed After Selector Refactor

This is a regression risk.

The original Chapter 20's reason for extracting the selector was to preserve the Chapter 6 behavior while giving RAG a second consumer. fileciteturn160file0L52-L54

If search behavior changes unexpectedly:

compare the current selector to the prior view logic,

inspect selector tests,

verify is_active=True,

verify all intended search fields,

verify deterministic ordering.

10. DestinationSearchResult Construction Fails

Check that all fields are supplied:

name
country
city
latitude
longitude
summary
description
tags

The current dataclass is frozen and requires these fields. fileciteturn153file0L2-L2

11. Decimal Serialization Problems

The current travel-planner path stores retrieved destination objects in an AgentRun snapshot.

Because latitude and longitude are Decimal, the service converts them to floats before storing the snapshot. fileciteturn158file0L2-L2

If snapshot serialization fails, inspect the conversion logic in run_travel_planner().

12. RAG Works but the LLM Gives a Poor Answer

First isolate retrieval from generation.

Step 1

Run:

docker compose exec web python manage.py shell -c "
from apps.ai_agents.destination_search import search_destination
results = search_destination(query='Japan')
for result in results:
    print(result)
"

Step 2

If retrieval is correct, inspect the prompt.

The prompt should contain:

Retrieved Destinations:

followed by the result fields. fileciteturn156file0L2-L2

Step 3

Only then investigate LLM behavior.

This prevents treating a retrieval problem as an LLM problem.

13. Old Chapter 20 Code Does Not Match Current Repository

The original documentation describes:

destination_search_tool.py
_search_destinations_executor
GroqClient.call_with_tools()

The current repository instead contains:

destination_search.py
apps/ai_agents/destination_search.py
ChatAgent.reply(retrieved_destinations=...)

This is expected repository evolution, not necessarily a broken implementation. fileciteturn160file0L189-L220 fileciteturn153file0L2-L2 fileciteturn154file0L2-L2

14. Current Retrieval Adapter Is Not Found

Expected location:

backend/apps/ai_agents/destination_search.py

Its responsibility is:

selector
  ↓
DestinationSearchResult[]

fileciteturn154file0L2-L2

15. Chat Agent Tests Fail

Check that ChatAgent.reply() still passes:

retrieved_destinations=retrieved_destinations or []

to the prompt. fileciteturn155file0L2-L2

The current test suite verifies that an explicitly supplied result is forwarded to the prompt. fileciteturn163file0L2-L2

16. Debugging the Retrieval Adapter

docker compose exec web python manage.py shell -c "
from apps.ai_agents.destination_search import search_destination

results = search_destination(query='Tokyo')

for result in results:
    print(result.name)
    print(result.country)
    print(result.city)
    print(result.summary)
    print(result.description)
    print(result.tags)
"

This bypasses the LLM entirely.

17. Debugging the Selector

docker compose exec web python manage.py shell -c "
from apps.destinations.selectors import search_destinations

results = search_destinations(query='tok')

print(
    list(
        results.values_list(
            'name',
            'country',
            'city',
        )
    )
)
"

18. Debugging Prompt Construction

Use a direct prompt instance and inspect:

conversation_context
retrieved_destinations
user_message

The prompt should produce the retrieval section only when results exist. fileciteturn156file0L2-L2

19. Rollback Strategy

This chapter introduces no new database schema.

Therefore rollback does not require data migration reversal.

The main rollback surfaces are:

selector changes
AI result contract
retrieval adapter
ChatAgent integration
prompt integration
service integration

The original chapter also identified the selector extraction as having no data implications because it is query logic. fileciteturn159file9L704-L720

20. Important Non-Implemented Claim

Do not claim that the current repository implements:

vector embeddings
vector database
semantic similarity
automatic embedding generation

The evidence reviewed for the current Chapter 20 implementation supports structured catalog retrieval instead.

21. Final Diagnostic Principle

Always debug RAG from left to right:

Database
   ↓
Selector
   ↓
Retrieval adapter
   ↓
Result object
   ↓
ChatAgent
   ↓
Prompt
   ↓
LLM

Do not start with the LLM when the retrieval chain has not yet been verified.