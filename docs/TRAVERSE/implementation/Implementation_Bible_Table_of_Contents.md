# Enterprise AI Travel Planner
## Engineering Implementation Bible — Table of Contents

**Source of truth:** *AI_Travel_Planner_Architecture_Handbook.md* (Phase 1, approved). Nothing in this Bible contradicts that document — it implements it, chapter by chapter, in the exact dependency order established in Sections 4 and 6 of the architecture handbook.

**Format:** Every chapter below follows the fixed 17-part template:
`1. Learning Objective → 2. Theory → 3. Architecture Decision → 4. Why Before How → 5. File Structure → 6. Folder Location → 7. Terminal Commands → 8. Docker Commands → 9. Expected Output → 10. Code → 11. Code Walkthrough → 12. Common Errors → 13. Debugging → 14. Testing → 15. Git Commit → 16. Checklist → 17. Next Chapter Preview`

**Rule:** Chapters are generated one at a time, on request ("Continue to Chapter X"). No chapter is skipped or merged.

---

## VOLUME 1 — Foundations

| Ch | Title | Builds |
|---|---|---|
| 1 | Repository, Environment & DockForge Verification | Confirms platform is healthy; no app code yet |
| 2 | Django Project Skeleton & App Registration | `config/`, `apps/` scaffold, `INSTALLED_APPS` wiring |

## VOLUME 2 — Identity & Core Domain

| Ch | Title | Builds |
|---|---|---|
| 3 | `core` App — Shared Foundations | `TimeStampedModel`, base mixins, exceptions, base permissions |
| 4 | `accounts` App — Custom User & Authentication | Custom `User` model, JWT auth, register/login/logout |
| 5 | `profiles` App — Traveler Preferences | `Profile` model, auto-creation signal, preferences API |
| 6 | `destinations` App — Reference Catalog | `Destination` model, seed data, search API |
| 7 | `trips` App — The Central Entity | `Trip` model, ownership permissions, CRUD API |

## VOLUME 3 — Trip Sub-Domains

| Ch | Title | Builds |
|---|---|---|
| 8 | `itinerary` App — Day-by-Day Planning | `ItineraryDay`, `ItineraryItem`, ordering logic |
| 9 | `budget` App — Cost Planning | `Budget`, `BudgetLineItem`, aggregation logic |
| 10 | `recommendations` App — Suggestion Engine (Data Layer) | `Recommendation` model, accept/reject workflow |

## VOLUME 4 — AI Layer

| Ch | Title | Builds |
|---|---|---|
| 11 | `ai/` Package Foundations | Groq client wrapper, prompt module structure, Pydantic output schemas |
| 12 | `ai_agents` App + Travel Planner Agent | Bridge app, `AgentRun` model, first LangGraph node |
| 13 | Budget Agent | Second graph node, numeric structured output |
| 14 | Weather Agent | Tool-calling pattern, external API integration |
| 15 | Recommendation Agent | Consumes itinerary + weather state |
| 16 | Packing Agent | Final graph node, full state consumption |
| 17 | LangGraph Orchestration Assembly | Wires all 5 agents into the full graph from Architecture Handbook §9.2; Celery task dispatch |

## VOLUME 5 — Conversational Layer

| Ch | Title | Builds |
|---|---|---|
| 18 | Memory & Conversation State | Short-term memory, state persistence pattern |
| 19 | `chat` App | `ChatSession`, `ChatMessage`, chat-to-agent bridge |
| 20 | Retrieval-Augmented Generation (RAG) | Destination knowledge retrieval layer |

## VOLUME 6 — Supporting Apps

| Ch | Title | Builds |
|---|---|---|
| 21 | `documents` App | PDF/itinerary export, shareable links |
| 22 | `notifications` App | Outbound notification dispatch (email first) |
| 23 | `bookings` App (Placeholder) | Future-facing model shell, no external integration yet |
| 24 | `analytics` App | Read-only aggregation, admin dashboards |

## VOLUME 7 — Hardening & Production

| Ch | Title | Builds |
|---|---|---|
| 25 | Full Testing Suite | Unit, integration, API, AI-mocked, regression tests across all apps |
| 26 | Security Hardening Pass | JWT hardening, rate limiting, prompt-injection defenses, audit logging |
| 27 | Performance & Caching Pass | `select_related`/`prefetch_related` audit, Redis caching, query optimization |
| 28 | CI/CD & Deployment | Using DockForge's existing prod compose + CI foundation, zero infra changes |
| 29 | Production Readiness Review | Final checklist, launch gate, retrospective template |

---

## How to Proceed

Say **"Continue to Chapter 1"** to begin. Each subsequent chapter is generated only on request, in order, never out of sequence, never merged with another chapter — matching the Architecture Handbook's phase discipline (§6) and app-creation order (§4).
