# Chapter 14 — Troubleshooting Guide

## Overview

Chapter 14 introduced the first tool-enabled AI agent into the TraVerse
platform. Unlike previous chapters, this implementation combined
multiple architectural layers:

- AI prompting
- tool execution
- structured validation
- planning graph orchestration
- Django persistence

Although the implementation was completed without architectural
regressions, several integration issues were encountered during
development. Each issue provided valuable insight into the interaction
between LangGraph, the AI layer, and the Django application.

This document records those issues, their root causes, and the adopted
solutions.

---

# Issue 1 — Weather Forecast Missing from Planning State

## Symptom

Planning Graph tests failed with:

```

KeyError: 'weather_forecast'

```

The Weather Agent executed successfully, but the final planning graph
state did not contain the generated weather forecast.

---

## Root Cause

LangGraph preserves only fields explicitly declared in the graph state
definition.

Although the Weather Agent returned:

```
weather_forecast
```

the canonical `PlanningGraphState` had not yet been extended to include
the new field.

Consequently, LangGraph silently discarded the additional value during
graph execution.

---

## Resolution

The planning state was updated with:

```
weather_forecast: NotRequired[WeatherForecastSchema]
```

After extending the state definition, LangGraph preserved the weather
forecast throughout the workflow and all planning graph tests passed.

---

# Issue 2 — Weather Tool Date Conversion

## Symptom

The Weather Agent attempted to execute the weather tool using an ISO
date string received from the language model.

The weather tool expected a strongly typed `date` object.

---

## Root Cause

LLM tool calls serialize arguments as JSON.

Consequently:

```
"2026-09-10"
```

was passed into the tool rather than:

```
date(2026, 9, 10)
```

The weather tool attempted to access calendar attributes on the string,
causing execution failure.

---

## Resolution

The Weather Agent converts the ISO string into a Python `date` object
before invoking the weather tool.

The conversion occurs only inside the agent, allowing the weather tool
to remain strongly typed and reusable.

---

# Issue 3 — Budget Fixture Constraint Violation

## Symptom

Django integration tests failed with a database integrity error similar
to:

```
duplicate key value violates unique constraint
```

---

## Root Cause

The Budget model enforces a one-to-one relationship between a trip and
its associated budget.

The test fixture unintentionally attempted to create multiple Budget
records for the same trip.

---

## Resolution

The fixture was updated to reuse the existing Budget instance rather
than creating a duplicate record.

This restored compatibility with the database constraints while keeping
the persistence logic unchanged.

---

# Issue 4 — Incorrect get_or_create Usage

## Symptom

Integration tests failed with an error similar to:

```
Cannot assign "(Budget, False)"
```

---

## Root Cause

`get_or_create()` returns a tuple:

```
(instance, created)
```

The tuple itself was accidentally assigned where a Budget model
instance was expected.

---

## Resolution

The tuple was correctly unpacked:

```
budget, _ = Budget.objects.get_or_create(...)
```

Only the Budget instance was passed to related models.

---

# Issue 5 — Docker Test Environment

## Symptom

The Docker container reported that pytest could not be found despite
being installed locally.

---

## Root Cause

The running container had been created before the project's Python
dependencies were updated.

The rebuilt image was not yet being used by Docker Compose.

---

## Resolution

The Docker image was rebuilt and the container recreated.

Verification was performed using:

```bash
python -m pytest --version
```

to confirm that the updated environment contained the required testing
tools.

---

# Issue 6 — Docker Compose Working Directory

## Symptom

Docker Compose reported:

```
The system cannot find the path specified.
```

when attempting to execute project commands.

---

## Root Cause

Compose commands were executed from the `backend` directory rather than
the repository root.

The relative path to the compose configuration therefore could not be
resolved.

---

## Resolution

Docker Compose commands were executed from the project root directory,
allowing the infrastructure configuration to be located correctly.

---

# Issue 7 — Planning Graph Regression Prevention

## Potential Risk

Introducing an additional AI agent could have required substantial
changes to the planning graph.

Such modifications would increase regression risk.

---

## Resolution

The workflow abstraction introduced during Chapter 13 allowed the
Weather Agent to be added simply by:

- creating a new workflow node
- registering the node
- extending the planning state

No modifications were required to the graph construction logic itself.

This confirmed that the orchestration architecture is genuinely
extensible.

---

# Issue 8 — Persistence Isolation

## Potential Risk

Weather persistence could accidentally overwrite itinerary content
generated by the Travel Planner Agent.

---

## Resolution

A dedicated persistence helper was implemented that updates only the
following fields:

- weather condition
- daily high temperature
- daily low temperature
- precipitation probability

All itinerary summaries, activities, and ordering remain untouched.

This preserves ownership boundaries between AI agents.

---

# Validation After Fixes

Every identified issue was resolved before the next implementation
phase began.

Validation was performed through:

| Validation Stage | Result |
|------------------|--------|
| AI Package Tests | ✅ 48 Passed |
| AI Integration Tests | ✅ 18 Passed |
| Platform Regression Tests | ✅ 193 Passed |

The successful completion of the entire regression suite confirmed that
each fix resolved the underlying issue without introducing additional
regressions.

---

# Key Takeaways

The issues encountered during Chapter 14 reinforced several important
engineering principles:

- LangGraph state definitions must include every value expected to flow
  between graph nodes.
- Tool boundaries should perform input adaptation while utility
  functions remain strongly typed.
- Persistence responsibilities should remain isolated from AI
  reasoning.
- Docker environments must be rebuilt whenever project dependencies
  change.
- Workflow extensibility significantly reduces implementation effort
  for future AI agents.

By resolving these integration issues early, the TraVerse AI platform
now possesses a stable foundation for future tool-enabled agents and
more advanced multi-agent orchestration.