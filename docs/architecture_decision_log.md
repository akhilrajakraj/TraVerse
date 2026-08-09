# TraVerse — Architecture Decision Log

**Status:** Living index. This file points to the chapter that contains the full reasoning; it does not duplicate the Architecture Decision sections.

**Rule:** Any future architecturally significant change must add or update an entry here as part of Definition of Done.

| # | Chapter | Decision | One-line summary |
|---:|---|---|---|
| 1 | Ch.4 | Custom User model, email-based identity | The user model is established before the first migration and is not replaced casually later. |
| 2 | Ch.7 | UUID for Trip, non-UUID reference data where appropriate | User-owned/shareable resources require enumeration-resistant identifiers; stable reference data does not automatically need UUIDs. |
| 3 | Ch.9 | Recalculate `computed_budget_total` | Correctness and drift prevention take priority over an incremental total that can become stale. |
| 4 | Ch.11 | Framework-independent `ai/` package | Core AI logic keeps Django dependencies out and owns its exception hierarchy. |
| 5 | Ch.12 | `ai_agents` is the single door into `ai/` | Django application code reaches the framework-independent AI layer through one controlled integration boundary. |
| 6 | Ch.13 | Do not bulk-create where signals are part of correctness | Per-row signal behavior is required where domain synchronization depends on it. |
| 7 | Ch.14 | Weather is seasonal/typical rather than a long-range live forecast | Long-horizon trip planning should not pretend that a live forecast remains meaningful months in advance. |
| 8 | Ch.15 | Separate AI regeneration strategies | Itinerary, budget, and recommendation regeneration use different policies because their correctness and user-impact characteristics differ. |
| 9 | Ch.16 | Correct the `packing_list` representation when evidence required it | Revisions are recorded as deliberate architecture corrections rather than hidden compatibility hacks. |
| 10 | Ch.19 | `chat` ↔ `ai_agents` dependency is an explicit exception | `ai_agents` remains the orchestration hub; the dependency is documented rather than treated as an accidental peer-to-peer cycle. |
| 11 | Ch.20 | RAG is implemented as a tool, not a vector database | The current structured catalog is small enough that a simpler retrieval mechanism is the right-sized solution. |
| 12 | Ch.21 | Share token is separate from `Document.id` | Resource identity and an access-granting secret are different concepts and must remain separate. |
| 13 | Ch.22 | Different deletion semantics for Notification and AgentRun actor references | `CASCADE` and `SET_NULL` are selected according to the meaning and durability requirements of each relationship. |
| 14 | Ch.24 | Analytics has no duplicate snapshot models | Existing domain facts remain the source of truth instead of being copied into a second analytics model. |
| 15 | Ch.26 | Audit-log actor uses durable deletion semantics | Audit history remains useful even when the original account no longer exists. |
| 16 | Ch.27 | Performance ceiling covers the full planning run | Query cost is evaluated across the combined multi-agent execution, not only isolated nodes. |
| 17 | Ch.28 | CI must not make real LLM calls | CI uses deterministic boundaries and independently enforced smoke-test safety so development activity cannot silently create provider cost or nondeterministic failures. |

## How to use this index

1. Find the relevant decision above.
2. Open the referenced chapter and read its **Architecture Decision** section for the complete rationale.
3. Before changing an established pattern, check whether the change is a deliberate revision that deserves a new ADR entry.
4. Add the new entry before the implementation is considered complete.

## Maintenance rule

This index is intentionally concise. If the reasoning needs to change, update the originating chapter (or create a new decision record) and then update this index. Do not turn this file into a second Architecture Handbook.