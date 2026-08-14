# Frontend Chapter 19 — Chat Interface Reconciliation

## Scope

Chapter 19 adds the trip-scoped conversational UI on top of the Chapter 18 chat state boundary. The implementation is frontend-only because the existing backend contract is sufficient.

## Audited backend contract

The authoritative endpoint is:

`POST /api/chat/trips/<trip_id>/chat/`

The request contains:

`{ "message": string }`

The response contains:

- `session_id`
- `assistant_message`
- `created_at`

The backend requires authentication, validates non-empty messages, limits messages to 4,000 characters, and applies its existing rate limit. The backend creates or reuses the active trip chat session as part of the request workflow.

## Frontend implementation

`TripChatPanel` is mounted on the existing trip detail page and uses the Chapter 18 `useChatState` hook.

Implemented behavior:

- Empty conversation state.
- User and assistant message presentation.
- Accessible message thread.
- Multiline message composer.
- 4,000-character input boundary matching the backend.
- Disabled send action for blank messages.
- Sending/assistant-response state.
- Error presentation with dismiss action.
- Failed-send draft restoration.
- Automatic scroll-to-latest-message behavior.
- Reuse of existing `Card`, `Button`, and project styling conventions.

## Deliberate non-changes

The backend does not currently expose a separate chat-history GET endpoint in the audited route contract. Therefore this chapter does not invent one and does not claim that a browser refresh hydrates prior messages. The current conversation state remains client-held after the Chapter 18 send workflow.

No backend files were modified for Chapter 19.

## Verification target

Before merge, run:

- `npm test`
- `npm run build`
- `git diff --check`

Focused tests cover the empty state, message rendering, trimmed submission, and failed-send draft restoration.
