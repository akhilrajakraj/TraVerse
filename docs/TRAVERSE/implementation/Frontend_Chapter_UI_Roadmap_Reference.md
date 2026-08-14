# TraVerse Frontend UI Roadmap Reference

## Purpose

This document is the persistent UI roadmap reference for the remaining frontend chapters. Every future chapter implementation must consult this file before coding, reconcile it against the current backend/frontend contracts, and implement only the chapter currently being worked on.

This roadmap is derived from the TraVerse React Frontend Implementation Bible TOC and reconciled with the repository's current architecture. The repository remains authoritative when an implementation differs from the original roadmap.

## Completed chapters

- Chapter 11 — AI Planner Trigger & Polling UI
- Chapter 12 — Agent Run Status & Live Progress Indicators
- Chapter 13 — Generated Itinerary Review UI

## Remaining UI chapters and planned features

### Chapter 14 — Weather Display UI
Backend integration: Backend Chapter 14 (`weather_*` fields)

Planned UI:
- Per-day weather card attached to the corresponding itinerary day.
- Weather condition text displayed from the backend's authoritative weather condition field.
- High and low temperature display in the backend's Fahrenheit contract.
- Precipitation probability display when the backend provides it.
- A small condition icon/presentation mapping based only on the backend condition value; no frontend weather sourcing or weather inference.
- Graceful missing-weather state when a day has no weather data.
- Weather loading/error behavior through the existing itinerary data flow.
- Responsive presentation that works alongside the Chapter 13 itinerary review UI.
- Focused tests for populated, partial/missing, and condition-mapping states.

Architecture rule: reuse the existing itinerary API/query and do not create a second weather API, polling system, weather provider, or AI behavior. If the backend response does not expose the existing `weather_*` model fields, add only the minimum serializer/API contract change required; do not redesign the itinerary backend.

### Chapter 15 — Recommendation Review UI (AI-Specific)
Backend integration: Backend Chapter 15

Planned UI:
- AI recommendation cards attached to the trip/planning result.
- Score-based ordering using the backend's recommendation score.
- Recommendation title, description, destination/context, and score presentation according to the actual serializer contract.
- Clear recommendation state presentation.
- Accept/reject interaction only if the backend exposes those mutations and permitted transitions.
- Loading, empty, error, and mutation states.
- Focused tests for ordering, rendering, and permitted actions.

### Chapter 16 — Packing List UI
Backend integration: Backend Chapter 16 (`PackingItem`)

Planned UI:
- Packing list grouped by backend-provided category.
- Checkbox/toggle for `is_packed` using the actual backend mutation contract.
- Packed/unpacked visual state.
- Item labels/details supported by the serializer.
- Empty/loading/error states.
- Mutation feedback and query invalidation through TanStack Query.
- Focused tests for grouping, toggling, and state transitions.

### Chapter 17 — Full AI Planning Flow Integration
Backend integration: Backend Chapter 17

Planned UI:
- One coherent trip-planning journey connecting Chapters 11–16.
- Generate-plan trigger and AgentRun lifecycle.
- Live status/progress presentation.
- Generated itinerary review.
- Weather enrichment.
- AI recommendations.
- Packing list.
- Correct refresh/invalidation boundaries between generated data sections.
- A coherent success state without inventing agent progress that the backend does not expose.
- Recovery/retry handling for actual backend terminal states.
- End-to-end integration tests for the complete frontend planning journey.

### Chapter 18 — Chat State Management
Backend integration: Backend Chapter 18

Planned UI/state:
- Client-side chat session state model.
- Conversation history state.
- Message lifecycle state.
- Optimistic message updates only where compatible with the backend contract.
- Pending/sending/error states.
- Query/cache boundaries for chat sessions and messages.

### Chapter 19 — Chat Interface — Conversational UI Component
Backend integration: Backend Chapter 19 (`chat`)

Planned UI:
- Chat session creation flow.
- Message thread UI.
- User/assistant message presentation.
- Composer/input and send action.
- Loading/sending state.
- Error/retry state.
- Scroll behavior appropriate to the existing design system.
- Session/message refresh behavior from the actual API contract.

### Chapter 20 — RAG-Aware Chat Enhancements
Backend integration: Backend Chapter 20

Planned UI:
- RAG/source-grounding affordance only when the backend exposes grounding metadata.
- Clear distinction between normal assistant responses and catalog-grounded responses.
- Source/context presentation only from authoritative backend data.
- No fabricated citations or confidence indicators.
- Tests for grounded and non-grounded responses.

### Chapter 21 — Documents — PDF Download & Public Share Page
Backend integration: Backend Chapter 21

Planned UI:
- Authenticated PDF/document generation or download action.
- Download progress/error state if exposed by the API.
- Share-link management UI.
- Public share page using the single intentionally unauthenticated route.
- Explicit routing verification so protected functionality is never exposed publicly.
- Expired/invalid share-link state.

### Chapter 22 — Notifications — Notification Center UI
Backend integration: Backend Chapter 22

Planned UI:
- Notification bell/entry point.
- Unread count.
- Notification list.
- Read/unread visual state.
- Mark-as-read interaction based on backend mutation support.
- Empty/loading/error states.

### Chapter 23 — Bookings — Wishlist/Intent UI
Backend integration: Backend Chapter 23

Planned UI:
- Minimal booking-intent or wishlist action supported by the actual placeholder contract.
- Clear pending/success/error state.
- No payment or reservation workflow unless the backend actually exposes it.

### Chapter 24 — Analytics — Admin Dashboard UI
Backend integration: Backend Chapter 24 (`analytics`, `IsAdminUser`)

Planned UI:
- Staff/admin-only dashboard.
- Summary metrics exposed by backend.
- Appropriate charts/tables for actual analytics responses.
- Loading/error/empty states.
- Permission-denied state.
- No client-side fabrication of metrics.

### Chapter 25 — Full Frontend Testing Suite
Planned work:
- Consolidate Vitest/React Testing Library coverage.
- API boundary mocks.
- Component tests.
- Feature integration tests.
- Cross-feature AI planning flow tests.
- Regression coverage for critical existing workflows.

### Chapter 26 — Accessibility & Security Hardening Pass
Planned work:
- Keyboard navigation audit.
- Semantic HTML and accessible names/roles.
- Focus management.
- Color/contrast review.
- Secure token-storage review.
- XSS/unsafe HTML review.
- CSRF/auth boundary review.
- Public-route security review.
- Removal of sensitive data from logs/UI/URLs where applicable.

### Chapter 27 — Performance & Bundle Optimization Pass
Planned work:
- Bundle inspection.
- Code splitting where justified.
- Lazy loading for appropriate routes/features.
- Memoization only where profiling justifies it.
- Query/cache optimization.
- Image/resource optimization.
- Lighthouse-driven fixes where available.

### Chapter 28 — CI/CD & Deployment
Planned work:
- Production frontend build pipeline.
- Environment configuration validation.
- Static hosting/CDN deployment configuration.
- CI test/build gates.
- Deployment-safe API base URL handling.
- No secrets in Vite-exposed variables.

### Chapter 29 — Production Readiness Review
Planned work:
- Final frontend functional verification.
- Cross-feature regression review.
- Accessibility/security/performance verification.
- CI/CD verification.
- Environment/configuration verification.
- Production launch checklist.
- Known limitations and technical-debt register.
- Final frontend retrospective.

## Mandatory implementation discipline for every remaining chapter

1. Inspect the current repository before coding.
2. Inspect the backend implementation before relying on an endpoint or field.
3. Treat the backend implementation as authoritative when documentation and code differ.
4. Search the existing frontend before creating a new API client, hook, type, query key, component, loading state, error state, empty state, or status mapping.
5. Reuse working shared infrastructure whenever possible.
6. Make the smallest safe change that satisfies the chapter.
7. Do not silently merge multiple chapters.
8. Backend modifications are allowed only when the current backend contract demonstrably cannot support the chapter; then make the smallest compatible change and test it.
9. Never invent AI behavior, weather sourcing, recommendation scoring, packing semantics, chat/RAG behavior, or backend state transitions in the frontend.
10. Every chapter must include focused tests and a full-suite/build verification before being called complete.
11. Record actual Git commit/PR information only when it has genuinely been created.

## Current execution pointer

**Next chapter: Chapter 14 — Weather Display UI.**

Before implementing Chapter 14, verify whether `ItineraryDaySerializer` exposes the model's `weather_condition`, `weather_high_f`, `weather_low_f`, and `weather_precipitation_chance` fields. If it does not, treat that as a backend/API contract gap and make only the minimal serializer/frontend type change necessary to expose already-persisted weather data. Do not modify the weather agent or AI orchestration for a presentation-layer requirement.
