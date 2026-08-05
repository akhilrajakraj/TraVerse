# Chapter 15 – Recommendation Agent

**Volume 4 – AI Layer**

# Troubleshooting

---

# Introduction

Chapter 15 introduces the first synchronized multi-agent workflow within TraVerse.

Unlike previous chapters, Recommendation generation depends on multiple upstream AI agents before execution. As a result, troubleshooting extends beyond individual AI agents and includes graph orchestration, graph state synchronization, recommendation persistence and domain integration.

This document records the most common implementation issues encountered during development together with their resolutions.

---

# Issue 1 — Recommendation Agent Never Executes

## Symptoms

- Travel Planner executes successfully.
- Budget Agent executes successfully.
- Weather Agent executes successfully.
- No recommendations are generated.
- Recommendation persistence is never reached.

## Cause

The Recommendation Agent was not added to the LangGraph workflow.

Typical causes include:

- missing workflow node
- missing graph edge
- node omitted from the workflow list

## Resolution

Verify that:

- the Recommendation Agent node exists
- the node has been added to the workflow
- the workflow terminates only after Recommendation execution

The planning graph should execute in the following order.

```
Travel Planner

↓

Budget

↓

Weather

↓

Recommendation

↓

END
```

---

# Issue 2 — Recommendations Missing From Graph State

## Symptoms

The Recommendation Agent executes successfully but downstream persistence cannot access:

```
recommendations
```

A KeyError or missing state entry may occur.

## Cause

`PlanningGraphState` was not updated with the Recommendation output.

LangGraph only preserves keys explicitly declared within the shared graph state.

## Resolution

Ensure `PlanningGraphState` contains:

```
recommendations:
    RecommendationBatchSchema
```

and that the Recommendation Agent returns the updated immutable state rather than mutating the existing state.

---

# Issue 3 — Recommendation Categories Are Rejected

## Symptoms

The Recommendation Agent completes successfully but persistence raises errors similar to:

```
ValueError:
'activity' is not a valid RecommendationCategory
```

or

```
ValidationError:
category does not match expected values
```

## Cause

The Recommendation Agent generated category values that differed from the Recommendation application's domain model.

The AI layer and Django domain model must share the same vocabulary.

## Resolution

Recommendation categories produced by the AI must exactly match the values defined by `RecommendationCategory`.

The AI schema and prompt should emit only supported categories rather than introducing translation logic during persistence.

---

# Issue 4 — Recommendations Are Never Persisted

## Symptoms

The Recommendation Agent produces valid output.

The planning graph completes successfully.

No Recommendation records appear in the database.

## Cause

Recommendation persistence was not integrated into the AI orchestration service.

Common causes include:

- `_persist_recommendations()` never called
- transaction exits before recommendation persistence
- recommendation output not included in the final graph state

## Resolution

Ensure recommendation persistence occurs after:

```
Persist Itinerary

↓

Persist Budget

↓

Persist Weather

↓

Persist Recommendations
```

within the existing database transaction.

---

# Issue 5 — Existing User Recommendations Disappear

## Symptoms

Accepted recommendations disappear after generating a new travel plan.

Rejected recommendations are also removed.

## Cause

The implementation deleted every recommendation instead of replacing only pending AI recommendations.

This violates the Recommendation regeneration strategy.

## Resolution

Only pending AI-generated recommendations should be removed.

Accepted recommendations must remain.

Rejected recommendations must remain.

Manual recommendations must also remain untouched.

---

# Issue 6 — Destination Resolution Fails

## Symptoms

Recommendation persistence silently skips recommendations or raises lookup errors.

## Cause

The Recommendation Agent returns destination names rather than Django model instances.

Persistence must resolve names into existing `Destination` records.

## Resolution

Resolve every recommendation against the Destination table before persistence.

If no matching destination exists, skip the recommendation rather than aborting the planning workflow.

This preserves referential integrity while keeping AI execution resilient.

---

# Issue 7 — Recommendation Tests Fail

## Symptoms

Recommendation persistence tests fail while existing itinerary, budget and weather tests continue to pass.

## Cause

Typical causes include:

- outdated recommendation schema
- graph state not updated
- recommendation persistence omitted
- invalid recommendation categories
- recommendation helper not invoked by the orchestration service

## Resolution

Validate the implementation incrementally.

Recommended validation order:

1. Recommendation Agent tests
2. Planning Graph tests
3. Recommendation persistence tests
4. AI service tests
5. Full regression suite

This isolates failures before running complete platform tests.

---

# Issue 8 — Transaction Rolls Back

## Symptoms

No itinerary, budget, weather or recommendation data is saved despite successful AI execution.

## Cause

Recommendation persistence participates in the same database transaction as every previous persistence step.

Any exception causes the entire transaction to roll back.

## Resolution

Identify the first exception raised inside the transaction.

Do not suppress persistence errors.

Instead, correct the underlying cause before retrying the planning workflow.

---

# Issue 9 — Graph State Appears Correct but Persistence Fails

## Symptoms

The planning graph returns a populated RecommendationBatchSchema.

Recommendation records are still not created.

## Cause

The AI layer intentionally does not perform persistence.

Persistence must occur through the Recommendations application service layer.

Direct ORM access bypasses application rules and may result in inconsistent behavior.

## Resolution

Always persist recommendations through the Recommendation service layer.

The AI orchestration layer should coordinate persistence rather than owning business logic.

---

# Issue 10 — Regression Tests Fail After Recommendation Changes

## Symptoms

Previously passing itinerary, budget or weather tests begin failing after modifying Recommendation functionality.

## Cause

Architectural boundaries have likely been violated.

Common causes include:

- Recommendation logic added to Budget Agent
- Recommendation logic added to Weather Agent
- graph state modified incorrectly
- persistence helper affecting unrelated modules

## Resolution

Maintain strict separation of responsibilities.

Each AI agent should continue to own exactly one capability.

Recommendation functionality should remain isolated from itinerary generation, budget estimation and weather forecasting.

---

# Summary

Most implementation issues encountered during Chapter 15 originate from synchronization between AI outputs, graph state contracts and Recommendation domain integration rather than from the Recommendation Agent itself.

Following the established architecture—immutable graph state, specialized AI agents, domain-owned persistence and comprehensive regression testing—ensures Recommendation generation integrates cleanly into the TraVerse multi-agent workflow while preserving maintainability and production reliability.