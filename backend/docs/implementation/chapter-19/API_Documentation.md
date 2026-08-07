# Chapter 19 – AI Conversational Assistant

# Document 08
# API Documentation

---

# 1. Introduction

The Chat API provides the primary communication interface between the TraVerse frontend and the conversational AI backend.

Unlike the AI layer, which is responsible for prompt engineering and language model interaction, the Chat API focuses on

- authentication
- authorization
- request validation
- conversation persistence
- AI orchestration
- response formatting

The API follows REST principles and integrates seamlessly with the existing TraVerse authentication system.

---

# 2. Endpoint Overview

Current endpoints implemented during Chapter 19

| Method | Endpoint | Description |
|----------|-------------------------------------------|------------------------------------------|
| POST | `/api/chat/trips/<trip_id>/chat/` | Send a chat message and receive an AI response |

Future endpoints may include

- Conversation history
- Conversation archive
- Conversation deletion
- Session listing
- Conversation export

---

# 3. Authentication

Authentication is mandatory.

The endpoint uses JWT authentication.

Example

```
Authorization:

Bearer <access_token>
```

Unauthenticated requests return

```
401 Unauthorized
```

---

# 4. Authorization

After authentication, ownership of the requested Trip is verified.

Workflow

```
Authenticated User

↓

Requested Trip

↓

Ownership Validation
```

If the Trip belongs to another user

```
404 Not Found
```

is returned.

No AI processing occurs.

---

# 5. Request URL

```
POST

/api/chat/trips/<trip_id>/chat/
```

Example

```
POST

/api/chat/trips/
8d21e760-1f0f-40af-bdb8-a4ec6f6dcf21/
chat/
```

---

# 6. Request Body

Content-Type

```
application/json
```

Example

```json
{
    "message": "Plan a three-day itinerary for Tokyo."
}
```

---

# 7. Request Validation

The request serializer validates

```
message
```

Rules

- required
- cannot be blank
- string

Invalid requests terminate before reaching the AI layer.

---

# 8. Successful Response

HTTP Status

```
200 OK
```

Example

```json
{
    "success": true,
    "assistant_message": "Here is a recommended three-day itinerary for Tokyo..."
}
```

Only the assistant response is returned.

Internal conversation state remains private.

---

# 9. Validation Error

Example request

```json
{
    "message": ""
}
```

Response

```
400 Bad Request
```

Example

```json
{
    "success": false,
    "errors": {
        "message": [
            "This field may not be blank."
        ]
    }
}
```

Validation occurs before

- session creation
- message persistence
- AI execution

---

# 10. Unauthorized Response

When no JWT token is supplied

```
401 Unauthorized
```

Example

```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

# 11. Forbidden Trip Access

When a user attempts to chat on another user's trip

```
404 Not Found
```

No information about the existence of the trip is leaked.

This protects user privacy.

---

# 12. Internal AI Failure

If the LLM raises an unexpected exception

the request terminates with

```
500 Internal Server Error
```

However

the user message has already been persisted.

This preserves conversation history.

---

# 13. Request Execution Pipeline

```
POST

↓

Authentication

↓

Authorization

↓

Serializer Validation

↓

Retrieve Active Session

↓

Persist User Message

↓

Conversation Memory

↓

Conversation Optimization

↓

Trip Context

↓

Chat Agent

↓

Groq

↓

Persist Assistant Response

↓

HTTP Response
```

---

# 14. Chat Session Behavior

Each Trip owns one active conversation.

Workflow

```
First Request

↓

Create Session

↓

Persist Messages

──────────────

Later Requests

↓

Reuse Session

↓

Append Messages
```

Conversation history continuously grows.

---

# 15. Conversation Persistence

For every successful request

the following messages are stored.

```
User Message

↓

Assistant Message
```

For failed AI requests

```
User Message

↓

LLM Failure

↓

Conversation Preserved
```

This behavior is verified by integration tests.

---

# 16. Conversation Ordering

Messages remain stored chronologically.

Example

```
User

↓

Assistant

↓

User

↓

Assistant

↓

User

↓

Assistant
```

Ordering is preserved throughout

- database
- memory
- prompt generation

---

# 17. Response Time Responsibilities

The API itself performs minimal work.

Heavy computation occurs inside

```
generate_chat_reply()
```

Responsibilities

- persistence
- memory generation
- prompt construction
- AI execution

This keeps API views lightweight.

---

# 18. Error Handling Strategy

| Layer | Responsibility |
|--------|----------------|
| Authentication | JWT validation |
| Authorization | Trip ownership |
| Serializer | Input validation |
| ChatService | Persistence |
| AI Service | AI orchestration |
| ChatAgent | LLM interaction |

Each layer handles only its own failures.

---

# 19. API Design Principles

The Chat API was designed around the following principles.

### Thin Views

Views coordinate requests only.

---

### Centralized Business Logic

Business logic remains inside services.

---

### Provider Independence

The API has no knowledge of Groq.

Changing providers requires no API changes.

---

### Consistent Responses

All responses follow the same project-wide response format.

---

### Separation of Concerns

Persistence

↓

AI

↓

HTTP

remain independent.

---

# 20. Future API Extensions

The current API can easily support

```
GET /history/

DELETE /conversation/

GET /sessions/

PATCH /session/

POST /stream/

POST /voice/

POST /summarize/
```

without major architectural changes.

---

# 21. API Sequence Diagram

```
Frontend

│

POST

│

▼

ChatAPIView

│

▼

Serializer

│

▼

ChatService

│

▼

generate_chat_reply()

│

▼

ConversationManager

│

▼

TripContextBuilder

│

▼

ChatAgent

│

▼

Groq

│

▼

Assistant Response

│

▼

HTTP Response
```

---

# 22. Summary

The Chat API provides a clean, secure, and extensible interface for conversational interaction within TraVerse.

By separating HTTP responsibilities from persistence, memory management, and AI orchestration, the API remains lightweight while supporting sophisticated conversational capabilities.

The implementation completed during Chapter 19 establishes a stable foundation for future enhancements such as conversation history retrieval, streaming responses, voice interaction, and advanced AI-assisted travel planning.

---
