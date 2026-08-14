# Frontend Chapter 18 — Chat State Management Reconciliation

## Scope

Chapter 18 establishes the frontend state boundary for the existing TraVerse chat API. It does not introduce a chat visual component; the conversational UI belongs to Chapter 19.

## Backend contract audited

The backend exposes an authenticated trip-scoped POST endpoint:

`POST /api/chat/trips/<trip_id>/chat/`

The request contract is:

```json
{
  "message": "..."
}
```

The response contract is:

```json
{
  "session_id": "uuid",
  "assistant_message": "...",
  "created_at": "..."
}
```

Persisted chat messages expose `id`, `role`, `role_display`, `content`, and `created_at`. Chat sessions expose their ordered messages, but the current public chat API does not expose a frontend-readable session-history GET endpoint. The current POST response also does not echo the persisted user-message record.

## Frontend decisions

- Use the shared `apiRequest()` gateway for authentication, refresh, error normalization, and the existing API base URL behavior.
- Keep chat conversation state local to the chat feature because the current API exposes no session-history query endpoint.
- Add the user's submitted message optimistically so the conversation can render immediately.
- Append the authoritative assistant response returned by the backend.
- Store the backend `session_id` returned by the chat endpoint.
- Do not invent a GET chat-history endpoint, session-creation endpoint, message-delete endpoint, streaming protocol, or server-side message status.
- Ignore blank messages at the state boundary, matching the backend serializer's non-empty message contract.
- Expose pending, error, and recovery state to the Chapter 19 UI.
- On a failed send, remove only the optimistic user message created for that request and expose the authoritative request error; no fake assistant message is generated.

## Deliberate limitation

Because the current backend contract does not provide a chat-history read endpoint, this state is not persisted across a full browser refresh by the frontend. Implementing persistence through local storage or inventing a read API would create semantics that the backend does not currently authorize. A future backend/API change can add a query boundary without changing the Chapter 19 presentation contract.

## Files

- `frontend/src/features/chat/api/chatApi.ts`
- `frontend/src/features/chat/hooks/useChatState.ts`
- `frontend/src/features/chat/__tests__/useChatState.test.ts`

## Verification

Focused tests were added for:

1. successful user → assistant state transition;
2. blank-message rejection at the state boundary;
3. failed send rollback and error recovery.

Before merge, run the complete frontend test suite and production build locally. Do not mark this chapter complete until both pass.
