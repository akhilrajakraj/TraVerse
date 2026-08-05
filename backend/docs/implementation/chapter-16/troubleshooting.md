# Chapter 16 — Troubleshooting

This document captures the engineering knowledge acquired during the implementation of the Packing Agent and its integration into the TraVerse planning architecture. Rather than recording isolated implementation issues, the objective is to explain the framework behaviour, architectural reasoning, and engineering decisions that influenced the final solution.

---

# Issue 1 — PackingItem Database Table Not Found

## Observation

Execution of the newly introduced packing persistence tests failed during object creation with a PostgreSQL relation error indicating that the `trips_packingitem` table did not exist.

The failure occurred before any application logic was executed, preventing the persistence layer from being validated.

---

## Root Cause

The `PackingItem` domain model had been implemented within the Trips application, but no database migration had yet been generated for the new model.

During automated testing, Django constructs an isolated test database exclusively from registered migrations. Since the migration responsible for creating the new table did not exist, the database schema remained incomplete despite the presence of the model in the source code.

---

## Framework Behaviour

Django's migration framework treats model definitions and database schema as separate concerns.

The ORM does not infer schema changes directly from model definitions during test execution. Instead, the test database is reconstructed entirely from migration history to guarantee deterministic and reproducible environments.

Consequently, any model introduced without a corresponding migration remains invisible to the database layer.

---

## Resolution

A dedicated migration was generated for the Trips application, introducing the `PackingItem` table into the database schema.

Following migration generation, both development and test databases correctly reflected the updated domain model, allowing persistence validation to proceed successfully.

---

## Architectural Improvement

The implementation reinforced the requirement that every domain model modification must be accompanied by an explicit migration before service-layer integration begins.

Migration generation therefore became an architectural checkpoint rather than a post-implementation activity.

---

## Engineering Principle

Domain models and relational schema evolve together.

Maintaining synchronization between source code and migration history is essential for deterministic deployments, reproducible testing, and operational stability.

---

# Issue 2 — AI Output Contract Drift

## Observation

Early persistence validation exposed inconsistencies between generated packing data and the application's expected schema.

Although the language model produced structurally similar information, categorical values and field names differed from those expected by downstream services.

---

## Root Cause

Language models naturally generate semantically reasonable output that may nevertheless violate strict application contracts.

Without explicit validation, structurally inconsistent responses could propagate into persistence logic and compromise application correctness.

---

## Framework Behaviour

The schema validation layer executes before persistence and rejects responses that fail structural or semantic validation.

This behaviour prevents invalid AI output from reaching the service layer while preserving the integrity of downstream domain models.

---

## Resolution

Dedicated packing schemas were introduced as the authoritative contract between the language model and the application.

Prompt engineering was refined to reinforce those contracts, ensuring that generated responses consistently satisfied schema validation before persistence.

---

## Architectural Improvement

The schema layer now serves as the exclusive interface between AI execution and application services.

Neither persistence logic nor domain models depend directly on raw language model output.

---

## Engineering Principle

Artificial intelligence should be treated as an external system.

Every response entering the application must undergo deterministic validation before interacting with domain logic.

---

# Issue 3 — Preserving User-Owned Packing Data

## Observation

Repeated execution of the planning workflow introduced the possibility of replacing previously generated packing lists.

Without careful separation, automated planning could overwrite manually maintained travel information.

---

## Root Cause

AI-generated data and user-managed data coexist within the same domain model while representing different ownership semantics.

Treating both categories identically would violate user expectations and compromise long-term data integrity.

---

## Framework Behaviour

Domain services provide a controlled persistence boundary capable of distinguishing AI-generated entities from manually managed records.

This enables selective replacement while preserving user-owned information.

---

## Resolution

Packing persistence was implemented to remove only AI-generated packing items before storing newly generated recommendations.

Manual packing entries remain unaffected across repeated planning executions.

---

## Architectural Improvement

Ownership semantics became an explicit architectural concern within the persistence layer rather than an implicit assumption of the planning workflow.

This design enables future manual editing capabilities without requiring modification to AI orchestration.

---

## Engineering Principle

Persistence strategies should reflect data ownership rather than implementation origin.

Automated systems may replace their own artifacts but should never assume authority over user-managed data.

---

# Issue 4 — Extending the Planning Graph

## Observation

Integrating an additional planning stage risked increasing coupling between autonomous planning agents.

Without careful orchestration, introducing the Packing Agent could have altered execution behaviour across existing planning components.

---

## Root Cause

The planning workflow coordinates multiple autonomous AI agents that operate sequentially on a shared planning state.

Introducing new responsibilities directly into existing agents would reduce modularity and complicate future expansion.

---

## Framework Behaviour

LangGraph represents planning execution as an explicit directed workflow.

Each node performs an isolated responsibility while exchanging validated state with neighbouring stages.

Additional planning capabilities therefore become workflow extensions rather than modifications to existing components.

---

## Resolution

The Packing Agent was introduced as an independent planning node consuming validated itinerary, weather, and trip information while producing a dedicated packing artifact.

Existing planning agents remained unchanged.

---

## Architectural Improvement

The planning graph continues to function as the authoritative orchestration layer for autonomous planning activities.

Future AI capabilities can be introduced by extending the workflow rather than modifying established planning stages.

---

## Engineering Principle

Workflow orchestration should evolve through composition rather than modification.

Independent planning stages preserve maintainability, extensibility, and architectural clarity.

---

# Issue 5 — Layered Validation Before Integration

## Observation

The Packing Agent affected multiple architectural layers simultaneously, including schemas, prompts, AI orchestration, persistence services, REST interfaces, and automated testing.

Integrating all components without intermediate verification would significantly increase debugging complexity.

---

## Root Cause

Large architectural changes introduce failure points across numerous framework boundaries.

Without incremental validation, identifying the origin of integration failures becomes increasingly difficult.

---

## Framework Behaviour

The testing infrastructure supports independent verification of individual architectural layers before full-system integration.

This enables failures to be isolated within the smallest possible implementation boundary.

---

## Resolution

Validation progressed incrementally through:

- schema validation
- planning graph validation
- AI service validation
- domain model validation
- serializer validation
- service-layer validation
- REST endpoint validation
- application regression testing
- platform-wide regression testing

Each layer was confirmed independently before progressing to the next stage.

---

## Architectural Improvement

Layered validation now forms a repeatable engineering workflow for introducing future AI planning capabilities into the platform.

This methodology significantly reduces integration risk while preserving confidence in architectural correctness.

---

## Engineering Principle

Validation should progress in the same direction as architectural dependencies.

Verifying individual layers before complete integration produces more reliable systems, shorter debugging cycles, and greater long-term maintainability.