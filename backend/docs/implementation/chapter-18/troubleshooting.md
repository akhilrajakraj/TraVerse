# Chapter 18 — Conversation Memory & Context Management

# Troubleshooting Guide

## Introduction

This document records every significant issue encountered during the implementation of the Conversation Memory subsystem.

Rather than documenting hypothetical problems, this guide captures the actual engineering issues that arose during development, explains their root causes, and records the final resolutions.

The objective is to simplify future maintenance while preserving the reasoning behind architectural and testing decisions.

---

# Issue 1

## Pytest Did Not Discover Any Tests

### Symptom

Running the memory summarizer tests produced:

```text
no tests ran
```

or

```text
collected 0 items
```

even though the test file existed.

---

## Cause

Pytest only discovers:

- functions beginning with `test_`
- classes beginning with `Test`

The original test classes were named:

```python
class MemorySummarizerInitializationTests
```

and

```python
class MemorySummarizerTests
```

Because neither class started with the prefix `Test`, pytest ignored every test contained within them.

---

## Resolution

Rename the classes to satisfy pytest discovery conventions.

Example:

```python
class TestMemorySummarizerInitialization
```

```python
class TestMemorySummarizer
```

No changes to test logic were required.

---

## Result

Pytest successfully collected every test.

Example:

```text
8 passed
```

---

# Issue 2

## ConversationMessage Construction Failed

### Symptom

Conversation manager tests immediately failed with:

```text
TypeError:
ConversationMessage.__init__()
missing required positional argument:
'timestamp'
```

---

## Cause

ConversationMessage requires three fields:

- role
- content
- timestamp

The tests only supplied:

```python
ConversationMessage(
    role="user",
    content="Hello",
)
```

The timestamp argument was omitted.

---

## Resolution

Each test now explicitly constructs messages using:

```python
ConversationMessage(
    role="user",
    content="Hello",
    timestamp=datetime.utcnow(),
)
```

The tests now accurately mirror the production API.

---

## Result

Initialization failures disappeared.

---

# Issue 3

## Summary Was Never Inserted

### Symptom

The test expected:

```text
Conversation Summary
```

as the first message.

Instead:

```text
Message 6
```

remained.

---

## Cause

ConversationManager stores the generated summary separately.

It assigns:

```python
memory.summary = summary
```

rather than inserting a synthetic ConversationMessage into the message list.

The original test incorrectly assumed that the summary became:

```python
memory.messages[0]
```

This assumption did not match the implementation.

---

## Resolution

The test was rewritten to verify the actual implementation.

Instead of asserting:

```python
memory.messages[0]
```

the test now checks:

```python
memory.summary
```

---

## Result

The test now validates the intended architecture instead of an incorrect assumption.

---

# Issue 4

## Incorrect Expectation for Preserved Messages

### Symptom

The preservation test expected:

```text
Message 6
Message 7
...
Message 11
```

The actual memory contained:

```text
Message 7
...
Message 11
```

---

## Cause

ConversationManager intentionally preserves a configurable number of recent messages.

The implementation preserves exactly the configured window.

The test incorrectly expected one additional historical message.

---

## Resolution

The expected preserved window was updated to match the implementation.

The preservation policy was confirmed to be functioning correctly.

---

## Result

Recent-message preservation tests now align with production behaviour.

---

# Issue 5

## Understanding Conversation Summary Storage

### Initial Assumption

The implementation originally appeared to replace historical messages with a synthetic summary message.

Example:

```text
Summary
Message 7
Message 8
...
```

---

## Actual Implementation

ConversationMemory stores summaries separately.

Internally it contains:

```text
summary

messages[]
```

rather than:

```text
messages[]
```

only.

This separation keeps summarized history independent from active conversational exchanges.

---

## Resolution

The test suite was updated to validate:

- summary field
- recent messages
- removed historical messages

rather than assuming summaries become messages.

---

# Issue 6

## Ensuring Mutation Rather Than Replacement

### Concern

ConversationManager performs optimization.

It was important to verify whether optimization returned:

- a new ConversationMemory object

or

- the existing instance.

Replacing the object could invalidate references held by downstream planning components.

---

## Resolution

A dedicated unit test verifies:

```python
returned_memory is memory
```

This guarantees in-place mutation.

---

## Result

The ConversationMemory object remains stable throughout its lifecycle.

---

# Issue 7

## Dependency Isolation During Testing

### Concern

Memory summarization invokes the Groq API.

Allowing real API calls during testing would produce:

- nondeterministic results
- network dependency
- slower execution
- unnecessary API costs

---

## Resolution

Every external dependency was mocked.

Examples include:

- GroqClient
- MemorySummarizerPromptV1
- MemorySummarizer

The tests validate orchestration rather than external inference.

---

## Result

Every memory test executes entirely offline.

---

# Issue 8

## Verifying Entire AI Test Suite

Following completion of the Conversation Memory subsystem, the complete AI test suite was executed to ensure no regressions had been introduced into earlier chapters.

Command executed:

```bash
pytest ai/tests -v
```

Result:

```text
69 passed
1 warning
```

The single warning originated from a LangGraph dependency regarding a future serializer configuration change.

No failures were produced.

No production code modifications were required.

---

# Lessons Learned

Several important engineering lessons emerged during Chapter 18.

## Respect Existing Architecture

Tests should validate implemented behaviour rather than assumptions.

Incorrect assumptions often indicate misunderstanding rather than implementation defects.

---

## Follow Framework Conventions

Pytest relies heavily on naming conventions.

Proper class and function names are essential for automatic discovery.

---

## Strongly Typed Domain Models

Requiring mandatory constructor fields improves data integrity but requires tests to construct realistic domain objects.

---

## Separate State from Representation

Conversation summaries are part of conversational state.

They are not conversational messages.

Maintaining this distinction results in a cleaner architecture.

---

## Prefer Dependency Injection

Injecting collaborators dramatically simplifies testing while reducing coupling between components.

---

## Final Validation

At the conclusion of Chapter 18:

- Memory summarization operated correctly.
- Conversation optimization preserved recent context.
- Historical summaries were stored correctly.
- Dependency injection functioned throughout the subsystem.
- Mock-based testing eliminated external API requirements.
- The entire AI module successfully passed all automated tests.

Final verification:

```text
69 tests passed
0 failures
```

The Conversation Memory subsystem is considered complete, validated, and ready for integration with subsequent chapters.