# Chapter 15 – Recommendation Agent

**Volume 4 – AI Layer**

# Architecture

---

# Architectural Goal

The primary objective of Chapter 15 is to transform the AI workflow from a collection of independent specialized agents into a coordinated multi-agent planning system.

Previous chapters established three specialized AI agents:

- Travel Planner
- Budget Agent
- Weather Agent

Each agent solved a single problem independently.

Chapter 15 introduces the first AI component capable of synthesizing the outputs produced by multiple upstream agents before generating its own structured result.

This represents the beginning of hierarchical AI orchestration within TraVerse.

---

# High-Level Architecture

```
                    ┌─────────────────────┐
                    │     Django API      │
                    └──────────┬──────────┘
                               │
                               ▼
                 apps.ai_agents.services
                               │
                               ▼
                    run_planning_graph()
                               │
                               ▼
                   LangGraph Planning Graph
                               │
      ┌────────────────────────┼────────────────────────┐
      │                        │                        │
      ▼                        ▼                        ▼
Travel Planner          Budget Agent          Weather Agent
      │                        │                        │
      └────────────────────────┴──────────────┐
                                              ▼
                                 Recommendation Agent
                                              │
                                              ▼
                                 RecommendationBatchSchema
                                              │
                                              ▼
                            apps.ai_agents.services
                                              │
                                              ▼
                    apps.recommendations.services
                                              │
                                              ▼
                                Recommendation Model
```

The Recommendation Agent does not communicate directly with Django models.

Instead it participates exclusively through validated graph state objects.

---

# Evolution of the Planning Graph

## Prior Architecture

After Chapter 14 the planning graph terminated after weather estimation.

```
Travel Planner
        │
        ├──────────────┐
        │              │
        ▼              ▼
 Budget Agent     Weather Agent
        │              │
        └────── END ───┘
```

Each downstream agent executed independently.

No synchronization existed.

---

## Chapter 15 Architecture

Chapter 15 introduces the first synchronization node.

```
                 Travel Planner
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
      Budget Agent          Weather Agent
             │                     │
             └──────────┬──────────┘
                        ▼
             Recommendation Agent
                        │
                        ▼
                       END
```

Execution of the Recommendation Agent begins only after both predecessor nodes complete successfully.

This pattern enables downstream AI agents to reason over multiple validated outputs.

---

# Recommendation Agent Responsibilities

The Recommendation Agent owns exactly four responsibilities.

1. Render the recommendation prompt.
2. Invoke the configured LLM client.
3. Validate structured output using Pydantic.
4. Return an updated `PlanningGraphState`.

The agent intentionally does **not**:

- access Django ORM
- query databases
- persist recommendations
- perform business validation
- communicate with application services

These responsibilities remain outside the AI layer.

---

# Recommendation Agent Inputs

Unlike previous AI agents, the Recommendation Agent consumes multiple validated inputs.

```
PlanningGraphState

├── trip_title
├── destination_names
├── trip_notes
├── itinerary
├── budget_estimate
└── weather_forecast
```

All inputs have already been validated before recommendation generation begins.

The Recommendation Agent never consumes Django models directly.

---

# Recommendation Agent Output

The Recommendation Agent produces one validated object.

```
RecommendationBatchSchema

└── recommendations[]

        ├── destination
        ├── category
        ├── score
        └── reason
```

The output becomes part of the shared graph state.

```
PlanningGraphState

├── itinerary
├── budget_estimate
├── weather_forecast
└── recommendations
```

This allows downstream orchestration layers to persist recommendations without coupling the AI agent to Django.

---

# Recommendation Prompt

The prompt builder follows the same architecture introduced in previous chapters.

```
RecommendationAgentPromptV1

├── VERSION
├── NAME
├── SYSTEM_PROMPT
└── render_user_prompt()
```

The rendered prompt combines:

- trip metadata
- itinerary
- budget estimate
- weather forecast

before requesting structured recommendation output.

---

# Recommendation Persistence

Persistence remains outside the AI layer.

```
Recommendation Agent

        │

        ▼

PlanningGraphState

        │

        ▼

apps.ai_agents.services

        │

        ▼

_persist_recommendations()

        │

        ▼

apps.recommendations.services

        │

        ▼

Recommendation
```

The AI layer never creates ORM objects directly.

All persistence flows through the Recommendations application service layer.

---

# Recommendation Regeneration Strategy

Recommendations differ from itinerary items.

Recommendations represent user decisions.

Because of this, regeneration follows a selective replacement strategy.

```
Existing Recommendations

        │

        ▼

Pending AI Recommendations

        │

Delete

        ▼

Accepted Recommendations

        │

Preserve

        ▼

Rejected Recommendations

        │

Preserve

        ▼

Insert New AI Recommendations
```

Only pending AI recommendations are removed.

Accepted and rejected recommendations remain untouched.

This preserves user intent across repeated AI executions.

---

# Destination Resolution

The Recommendation Agent returns destination names.

Before persistence, each recommendation is matched against an existing `Destination`.

```
Recommendation

Destination Name

        │

        ▼

Destination.objects.filter()

        │

        ▼

Destination Instance

        │

        ▼

create_recommendation()
```

Recommendations referencing unknown destinations are skipped.

This guarantees referential integrity without interrupting the planning workflow.

---

# Transaction Boundary

Recommendation persistence participates in the existing transaction.

```
transaction.atomic()

│

├── Persist Itinerary

├── Persist Budget

├── Persist Weather

└── Persist Recommendations
```

A failure in any persistence step rolls back the complete AI execution.

This prevents partially updated travel plans.

---

# Architectural Principles

Chapter 15 preserves every architectural rule established in previous chapters.

- AI agents remain independent of Django.
- Business logic remains inside application services.
- Graph state remains immutable.
- Structured schemas define inter-agent contracts.
- LangGraph owns workflow orchestration.
- Persistence remains transactional.
- Recommendation generation is deterministic through validated outputs.

No architectural boundaries introduced in earlier chapters are violated.

---

# Chapter Outcome

Chapter 15 completes the transition from independent AI agents to a coordinated multi-agent planning architecture.

The Recommendation Agent demonstrates how downstream agents can consume multiple validated AI outputs while preserving strict separation between orchestration, domain services and persistence.

This synchronization model becomes the architectural foundation for future composite AI capabilities within TraVerse.