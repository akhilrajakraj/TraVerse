# Enterprise AI Travel Planner
## Engineering Architecture & Development Handbook

**Document Type:** Internal Engineering Blueprint
**Status:** Pre-Implementation (No code has been written yet)
**Built On:** DockForge (frozen infrastructure platform)
**Audience:** Engineers learning enterprise backend architecture

> This document is the single source of truth for how this project is designed, why it is designed that way, and in what order it will be built. Nothing in this project should be built without first locating it in this handbook.

---

## How To Read This Document

Two layers exist in this project, and they must never blend:

| Layer | Name | Owns | Status |
|---|---|---|---|
| Platform Layer | **DockForge** | Docker, Compose, Postgres, Redis, Nginx, Gunicorn, logging, health checks, env management, dev/prod configs | **Frozen.** Not redesigned, not modified structurally. |
| Application Layer | **AI Travel Planner** | Django apps, models, views, serializers, AI agents, templates, business logic | **This project.** Everything we build lives here. |

Think of DockForge as the **building** — foundation, plumbing, electricity, elevators, already inspected and approved. The AI Travel Planner is the **business that moves into the building** — it arranges furniture, hires staff, and serves customers. We never touch the plumbing. We only occupy floors.

Every section below is written so a beginner can follow it. Every new idea is explained before it's used.

---

# SECTION 1 — Project Vision

### 1.1 The Real-World Problem (ELI10)

Imagine you want to go on a trip. You have to:
- Google "best places to visit in Japan"
- Open 10 browser tabs comparing hotels
- Guess how much money you'll need
- Make a packing list yourself
- Try to remember the weather
- Write your own day-by-day plan

That's exhausting. A human travel agent used to do this for you, but that costs money and takes time. **This project builds a digital travel agent that never sleeps** — an AI that plans your entire trip, manages your budget, gives recommendations, and remembers your preferences, all inside one application.

### 1.2 Why This Project Exists

- **Real problem:** Trip planning is fragmented across many tools (maps, budgeting apps, notes apps, search engines).
- **Our solution:** One platform where a user describes a trip in plain language and an AI system plans it end-to-end — itinerary, budget, packing, recommendations — while a normal Django backend stores and manages everything reliably.

### 1.3 Target Users

| User Type | Need |
|---|---|
| Solo traveler | Fast, personalized itinerary without research fatigue |
| Family planner | Budget-aware, multi-day structured plans |
| Frequent business traveler | Quick, reliable, repeatable trip generation |
| Backpacker / budget traveler | Cost optimization and packing help |
| (Future) Travel agency staff | Bulk trip generation, admin oversight |

### 1.4 Business Goals

1. Prove that an AI-native product can be layered cleanly on reusable infrastructure (DockForge), reducing time-to-market.
2. Create a platform extensible into a real commercial product (bookings, marketplace — see Section 13).
3. Demonstrate a defensible architecture that could be shown to employers/investors as production-grade, not "hackathon-grade."

### 1.5 Technical Goals

1. Strict separation of platform vs application concerns.
2. A Django backend that is modular, testable, and independently deployable app-by-app.
3. An AI layer (LangChain + LangGraph) that is swappable, observable, and cost-controlled — not a black box tangled into views.
4. A system that could survive a real code review at a serious engineering org.

### 1.6 Learning Goals (Why This Project Teaches You Enterprise Engineering)

By finishing this project you will have practiced, in order:
1. Layered system design (platform vs application)
2. Django app decomposition at enterprise scale
3. Relational database modeling for a non-trivial domain
4. REST API design discipline
5. Multi-agent AI system design (not "one big prompt")
6. Async task processing (Celery + Redis)
7. Production deployment thinking (even though infra is frozen, you must *understand* it to use it correctly)
8. Testing discipline across a mixed AI/non-AI codebase
9. Security practices specific to LLM-integrated apps (prompt injection, etc.)

**Why this matters before you write code:** In real engineering orgs, the cost of a wrong decision made in Week 1 (e.g., a bad model boundary) can cost months later. Architecture-first is not bureaucracy — it's cheaper than the alternative.

---

# SECTION 2 — System Architecture

### 2.1 High-Level Architecture (ELI10)

Think of the whole system as a restaurant:
- **Nginx** = the host who greets guests at the door and shows them to a table (routes traffic).
- **Gunicorn** = the kitchen manager who assigns each order to a cook (runs Django worker processes).
- **Django (Application Layer)** = the cooks who actually make the food (business logic).
- **PostgreSQL** = the pantry/fridge where all ingredients (data) are permanently stored.
- **Redis** = the small prep counter next to the stove — fast, temporary, for things needed right now (cache, task queue, session broker).
- **Celery** = a second team of cooks who handle slow dishes (long AI generations) in the back, so the front-of-house cook isn't stuck waiting.
- **AI Layer (LangChain/LangGraph)** = a specialist chef (the "AI agent team") who is called in only for dishes that require creative recipes (itineraries, recommendations).

### 2.2 The Five Logical Layers

```
┌──────────────────────────────────────────────────────────────┐
│  1. INFRASTRUCTURE LAYER (DockForge — FROZEN)                 │
│     Docker, Compose, Nginx, Gunicorn, Postgres, Redis          │
├──────────────────────────────────────────────────────────────┤
│  2. PLATFORM SERVICES LAYER (DockForge — FROZEN)               │
│     Django base settings, logging, health checks, env mgmt     │
├──────────────────────────────────────────────────────────────┤
│  3. APPLICATION LAYER (THIS PROJECT)                            │
│     Django apps: accounts, trips, destinations, itinerary, ...  │
├──────────────────────────────────────────────────────────────┤
│  4. AI LAYER (THIS PROJECT)                                     │
│     LangChain, LangGraph, agents, prompts, memory, tools         │
├──────────────────────────────────────────────────────────────┤
│  5. DATA LAYER (Postgres = permanent, Redis = fast/temporary)   │
└──────────────────────────────────────────────────────────────┘
```

**Why this order matters:** each layer only depends on the layer(s) below it, never above. The AI layer never touches Nginx. The application layer never redefines Docker. This is called a **unidirectional dependency graph** — it prevents circular messes that are painful to untangle later.

### 2.3 Request Flow (What happens when a user clicks "Generate My Trip")

```
 [Browser]
    │  HTTPS request
    ▼
 [Nginx]  ──── serves static files directly, forwards dynamic requests
    │
    ▼
 [Gunicorn]  ──── spins up a Django worker to handle the request
    │
    ▼
 [Django View / DRF API]
    │
    ├──► [PostgreSQL] : read/write trip, user, destination data
    │
    ├──► [Redis]       : check cache, check rate limit
    │
    └──► If AI needed:
             │
             ▼
        [Celery Task Queued] ──► [Redis as broker] ──► [Celery Worker]
             │
             ▼
        [LangGraph Orchestrator]
             │
             ├──► [Travel Planner Agent]
             ├──► [Budget Agent]
             ├──► [Recommendation Agent]
             ├──► [Weather Agent]
             └──► [Packing Agent]
             │
             ▼
        [Groq LLM API] (the actual "thinking")
             │
             ▼
        Structured JSON result saved back to PostgreSQL
```

### 2.4 Response Flow

```
 [PostgreSQL row updated] 
       │
       ▼
 [Django serializes result to JSON]
       │
       ▼
 [Gunicorn returns response]
       │
       ▼
 [Nginx forwards to browser]
       │
       ▼
 [Frontend renders itinerary/budget/etc.]
```

**Why AI calls go through Celery instead of directly inside the web request:** LLM calls can take 5–30 seconds. If we made the user's browser wait on that inside the same request, we'd block a Gunicorn worker, which under load causes the whole site to slow down for *everyone*, not just that user. Offloading to Celery keeps the web layer fast and responsive — this is a standard enterprise pattern called **asynchronous task offloading**.

### 2.5 Why Layers Are Separated This Way

| Layer | If we DIDN'T separate it... |
|---|---|
| Infra vs App | Every project would reinvent Docker/Nginx config — huge wasted effort, and infra bugs would mix with business bugs. |
| App vs AI | Swapping LLM providers (Groq → OpenAI) would mean rewriting Django views — instead, only the AI layer changes. |
| Data (Postgres vs Redis) | Using only Postgres for temporary session/cache data would be slow and wasteful; using only Redis for permanent data would risk data loss. |

---

# SECTION 3 — Complete Folder Architecture

### 3.1 The Full Django Project Tree (Application Layer Only)

```
ai_travel_planner/                     # Django project root (lives INSIDE DockForge, doesn't replace it)
│
├── config/                            # Django project settings package
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py                    # Shared settings (imports DockForge platform settings)
│   │   ├── dev.py                     # Local overrides
│   │   └── prod.py                    # Production overrides
│   ├── urls.py                        # Root URL router
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py                      # Celery app bootstrap
│
├── apps/                              # ALL business-logic Django apps live here
│   ├── accounts/                      # Custom user model, auth
│   ├── profiles/                      # Traveler preferences/profile data
│   ├── trips/                         # Core "Trip" entity
│   ├── destinations/                  # Destination/location catalog
│   ├── itinerary/                     # Day-by-day plan entity
│   ├── budget/                        # Budget planning & tracking
│   ├── recommendations/               # AI-driven suggestions
│   ├── bookings/                      # (future) booking placeholder
│   ├── documents/                     # Trip documents, exports (PDF itinerary etc.)
│   ├── notifications/                 # Email/push/in-app notices
│   ├── chat/                          # Conversational interface to AI
│   ├── ai_agents/                     # LangChain/LangGraph agent orchestration
│   ├── analytics/                     # Usage tracking, admin dashboards
│   └── core/                          # Shared utilities, base models, mixins
│
├── ai/                                # AI layer — NOT a Django app, pure Python package
│   ├── agents/                        # One file per agent (planner, budget, etc.)
│   ├── graphs/                        # LangGraph workflow definitions
│   ├── prompts/                       # Prompt templates (versioned)
│   ├── tools/                         # Tool functions agents can call
│   ├── memory/                        # Conversation memory management
│   ├── parsers/                       # Structured output parsers/schemas
│   └── clients/                       # LLM client wrappers (Groq, fallback providers)
│
├── api/                               # DRF API layer — routers & versioning
│   └── v1/
│       ├── urls.py
│       └── (per-app serializers/viewsets are re-exported here)
│
├── templates/                         # Server-rendered templates (if using Django templates)
│   ├── base.html
│   └── (per-app subfolders)
│
├── static/                            # CSS/JS/images (source, pre-collectstatic)
│
├── tests/                             # Project-wide integration/e2e tests
│   ├── integration/
│   └── e2e/
│
├── docs/                              # THIS handbook + ADRs (Architecture Decision Records)
│   └── adr/
│
└── manage.py
```

**Important:** Nothing above touches `docker-compose.yml`, `nginx.conf`, `Dockerfile`, or DockForge's settings base. Those already exist and are frozen.

### 3.2 Why Each Top-Level Folder Exists

| Folder | Why It Exists | Scales How |
|---|---|---|
| `config/` | One place to control Django-wide wiring, so no setting is ever hunted for | Add `staging.py` later without touching `base.py` |
| `apps/` | Every business concept gets its own isolated, testable Django app | Add new apps (`bookings`, `payments`) without touching existing ones |
| `ai/` | Kept OUTSIDE Django apps intentionally — AI logic is pure Python, easier to unit test without spinning up Django, and easier to eventually extract into its own microservice | Can become a separate service later with minimal rewrite |
| `api/` | Centralizes REST versioning (`v1`, `v2`) instead of scattering it | Add `v2/` when breaking changes are needed, without breaking old clients |
| `templates/` & `static/` | Classic Django convention, kept if server-rendered UI is used alongside/instead of a SPA | Can be dropped entirely if frontend becomes a separate SPA |
| `tests/` | Cross-app tests that don't belong to any single app | Grows independently of app-level `tests.py` files |
| `docs/` | Prevents "tribal knowledge" — decisions are written down, not just remembered | ADRs accumulate over the life of the project |

### 3.3 Why `ai/` Is NOT a Django App

This is a deliberate, important decision (revisited formally in Section 15). Django apps are built around **models + migrations + admin + views**. The AI layer doesn't need any of that — it needs **pure functions that take input and return structured output**. Forcing it into a Django app structure would add unnecessary coupling (e.g., needing to run migrations to change a prompt). Keeping it a plain Python package means:
- It can be tested with plain `pytest`, no Django test runner needed.
- It could be extracted into a standalone microservice later with almost no rewrite.
- Django apps call *into* `ai/`, never the reverse — one-directional dependency, same principle as Section 2.

---

# SECTION 4 — Application Modules (Django Apps)

### 4.1 Order-of-Creation Philosophy (ELI10)

You don't build a car by installing the seats before the frame exists. Each app below is only created once the apps it depends on already exist. The table gives the **creation order** — this is not arbitrary, it's dictated by dependencies.

### 4.2 Full App Catalog

| # | App | Purpose | Depends On | Future Expansion |
|---|---|---|---|---|
| 1 | `core` | Shared base models (e.g. `TimeStampedModel`), shared mixins, custom exceptions | Nothing (foundation) | Shared permissions, shared pagination classes |
| 2 | `accounts` | Custom user model, authentication, JWT issuance | `core` | SSO, social login, MFA |
| 3 | `profiles` | Traveler preferences (budget style, interests, dietary needs) | `accounts` | Preference-based ML personalization |
| 4 | `destinations` | Catalog of places (cities, countries, points of interest) | `core` | Partner data feeds, geo-search |
| 5 | `trips` | The central "Trip" entity — dates, travelers, status | `accounts`, `destinations` | Trip templates, cloning |
| 6 | `itinerary` | Day-by-day plan generated for a trip | `trips`, `destinations` | Manual drag-and-drop editing |
| 7 | `budget` | Cost estimation & tracking per trip | `trips` | Real currency conversion, expense receipts |
| 8 | `recommendations` | AI-surfaced suggestions (restaurants, activities) | `trips`, `destinations` | Personalized ranking model |
| 9 | `ai_agents` | Django-facing bridge to the `ai/` package; stores agent run logs | `trips`, `itinerary`, `budget`, `recommendations` | Agent versioning, A/B testing prompts |
| 10 | `chat` | Conversational UI backend, message history | `accounts`, `ai_agents` | Voice input, multi-turn planning sessions |
| 11 | `documents` | Export itinerary to PDF, shareable links | `trips`, `itinerary` | Branded PDF templates, calendar (.ics) export |
| 12 | `notifications` | Email/push notices (trip ready, reminders) | `accounts` | SMS, WhatsApp integration |
| 13 | `bookings` | (Future placeholder) booking intent capture | `trips` | Real flight/hotel API integration |
| 14 | `analytics` | Usage metrics, admin dashboards | All apps (read-only) | Business intelligence exports |

### 4.3 Why This Specific Order

```
core
 └─► accounts
      └─► profiles
      └─► destinations (parallel, no user dependency)
           └─► trips (needs BOTH accounts + destinations)
                └─► itinerary
                └─► budget
                └─► recommendations
                     └─► ai_agents (needs trips/itinerary/budget/recommendations to exist as targets)
                          └─► chat
                          └─► documents
                          └─► notifications
                               └─► bookings (future)
                               └─► analytics (last — it just reads everything)
```

**Rule of thumb taught here:** an app can only be built once every app it has a foreign key to already exists and is migrated. This avoids Django migration dependency headaches and, more importantly, forces you to think about data ownership before code ownership.

### 4.4 Per-App Responsibility Notes (Beginner Explanations)

- **`accounts`**: "Who is allowed in the building." Owns login, registration, permissions. Nothing else should manage passwords or tokens — single source of truth.
- **`profiles`**: "What this person likes." Kept separate from `accounts` because account = identity, profile = preferences — they change at different rates and are queried differently.
- **`destinations`**: "The catalog of places in the world we know about." This is reference data, not user-owned data — it doesn't have a `user` foreign key.
- **`trips`**: "The contract." A trip is the central object everything else attaches to (itinerary, budget, recommendations all point back to a trip).
- **`itinerary`**: "The day-by-day script" for a trip.
- **`budget`**: "The money math" for a trip, kept separate from itinerary because budget can be edited independently and has different validation rules (currency, totals).
- **`recommendations`**: "Suggestions" — read-mostly, AI-populated, user can accept/reject.
- **`ai_agents`**: The **only** Django app allowed to import from the `ai/` package. This is a firewall — no other app is allowed to call an LLM directly. Enforced by code review discipline, not by a technical lock (documented as a rule, see Section 15).
- **`chat`**: The conversational front door to `ai_agents` — stores message history, but delegates actual "thinking" to `ai_agents`.
- **`documents`**: Turns structured data into shareable artifacts (PDF, links).
- **`notifications`**: One-way outbound communication, decoupled so any app can trigger a notification without knowing *how* it's delivered.
- **`analytics`**: Read-only consumer of everything else — never writes to other apps' tables directly, only reads (through APIs or read replicas later).

---

# SECTION 5 — Database Planning

### 5.1 ELI10: What Is an ER Diagram and Why Design Before Coding

Imagine building furniture without a diagram of how the pieces bolt together — you'd drill holes in the wrong place and have to redo it. An **Entity-Relationship (ER) Diagram** is that furniture diagram, but for data. We decide *which tables exist and how they connect* before writing a single Django model, because changing a foreign key after real data exists is expensive (data migrations, downtime risk).

### 5.2 Core Entities

| Entity | Owns | Notes |
|---|---|---|
| `User` | Identity, auth | Custom user model (email-based) |
| `Profile` | Preferences | One-to-one with `User` |
| `Destination` | Reference place data | Not user-owned |
| `Trip` | Trip metadata | Belongs to a `User`, references `Destination`(s) |
| `ItineraryDay` | One day of a trip | Belongs to `Trip` |
| `ItineraryItem` | One activity within a day | Belongs to `ItineraryDay`, may reference `Destination` (POI) |
| `Budget` | Overall budget envelope | One-to-one with `Trip` |
| `BudgetLineItem` | Individual cost line | Belongs to `Budget` |
| `Recommendation` | AI-suggested item | Belongs to `Trip`, may reference `Destination` |
| `AgentRun` | Log of an AI agent execution | Belongs to `Trip`, references `User` |
| `ChatSession` | A conversation thread | Belongs to `User`, optionally linked to `Trip` |
| `ChatMessage` | One message | Belongs to `ChatSession` |
| `Notification` | Outbound message record | Belongs to `User` |
| `Document` | Exported artifact | Belongs to `Trip` |

### 5.3 ER Diagram (ASCII)

```
 User (1)───(1) Profile
   │
   │ (1)───(M)
   ▼
  Trip ────────────(M)───(M)──── Destination
   │  │  │                          ▲
   │  │  │                          │ (referenced by)
   │  │  └──(1)──► Budget           │
   │  │              └──(1)─(M)──► BudgetLineItem
   │  │                              
   │  └──(1)──(M)──► ItineraryDay ──(1)─(M)──► ItineraryItem ──(M)──►(0..1) Destination
   │
   ├──(1)─(M)──► Recommendation ──(M)──►(0..1) Destination
   ├──(1)─(M)──► AgentRun
   ├──(1)─(M)──► Document
   └──(0..1)─(M)──► ChatSession ──(1)─(M)──► ChatMessage

 User ──(1)─(M)──► Notification
```

### 5.4 Relationship Types Explained (ELI10)

| Type | Meaning | Example Here |
|---|---|---|
| One-to-One | Exactly one of each side, always paired | `User` ↔ `Profile` |
| One-to-Many | One "parent" has many "children" | `Trip` → many `ItineraryDay` |
| Many-to-Many | Both sides can have many of the other | `Trip` ↔ `Destination` (a trip can span multiple cities; a city can appear in many trips) |

### 5.5 Normalization

We use **Third Normal Form (3NF)** as the default: every non-key field depends only on the primary key, not on other non-key fields. Example: `BudgetLineItem` stores `amount` and `category`, but NOT a recomputed `trip_total` (that's derived — computed on read or via a signal, never duplicated as stored truth). This avoids the classic bug where two copies of the "same" number drift apart.

**Deliberate denormalization (exception):** `Trip` may cache a `computed_budget_total` field, refreshed via signal, purely for fast dashboard reads. This is documented as an explicit trade-off (see Section 15), not an accident.

### 5.6 Indexes

| Table | Index | Why |
|---|---|---|
| `Trip` | `(user_id, status)` | Dashboard queries filter "my active trips" constantly |
| `ItineraryItem` | `(itinerary_day_id, order)` | Items are always fetched in day order |
| `ChatMessage` | `(chat_session_id, created_at)` | Messages always fetched chronologically |
| `AgentRun` | `(trip_id, agent_type, created_at)` | Debugging/analytics query by agent type over time |

### 5.7 Constraints

- `Budget.trip` → `unique=True` (enforces one-to-one at DB level, not just app level).
- `BudgetLineItem.amount` → `CheckConstraint(amount__gte=0)`.
- `Trip.end_date` → `CheckConstraint(end_date__gte=start_date)`.
- `Profile.user` → `unique=True`, `on_delete=CASCADE` (profile is meaningless without the user).

### 5.8 Foreign Key Delete Behavior (Why It Matters)

| Relationship | on_delete | Reasoning |
|---|---|---|
| `Trip.user` | `CASCADE` | If a user is deleted, their trips shouldn't orphan in the DB (GDPR-friendly too) |
| `ItineraryItem.destination` | `SET_NULL` (nullable) | Deleting a destination shouldn't destroy someone's itinerary — just detach the reference |
| `BudgetLineItem.budget` | `CASCADE` | Line items are meaningless without their parent budget |
| `AgentRun.trip` | `CASCADE` | Logs are only meaningful in context of the trip |

### 5.9 Future Migrations To Plan For (Not Built Now, But Reserved)

- `bookings` app will add `Booking` with FKs to `Trip` and eventually a `PaymentTransaction`.
- Multi-currency support will require a `Currency` reference table and converting `amount` fields to `(amount, currency)` pairs.
- Collaborative trips (Section 13) will require a `TripCollaborator` many-to-many through-table between `User` and `Trip` with a `role` field.

**Why plan migrations now, even unbuilt ones:** naming and shaping today's tables with tomorrow's additions in mind avoids painful renames later (e.g., we name the field `amount` not `price`, anticipating `BudgetLineItem` reuse patterns across `bookings` later).

---

# SECTION 6 — Development Roadmap (Phased Build Order)

### 6.1 Why Phases Exist (ELI10)

You wouldn't paint a house before the walls are built. Each phase below can ONLY start once the phase before it is done, because it literally depends on artifacts (files, tables, configs) that don't exist yet otherwise.

### 6.2 The Full Phase Chain

```
Phase 0 — Repository & Environment
  Repository Setup
    ↓
  Environment Verification (.env, secrets present)
    ↓
  Infrastructure Validation (docker compose up, Postgres/Redis reachable, DockForge health check green)
    ↓
Phase 1 — Django Skeleton
  Create Django Apps (empty apps/ folders, per Section 4 order)
    ↓
  Configure Settings (wire apps into DockForge's base settings, DO NOT edit DockForge itself)
    ↓
  Register Apps (INSTALLED_APPS)
    ↓
  Create Base Templates (base.html, layout partials) [if using server-rendered UI]
    ↓
Phase 2 — Identity Foundation
  Authentication Planning (decide session vs JWT — see Section 12)
    ↓
  Custom User Model (MUST be first migration — Django cannot swap user models later without pain)
    ↓
  Migrations (initial migration run against Postgres)
    ↓
  Admin Configuration (register User in admin for manual inspection)
    ↓
  Login
    ↓
  Registration
    ↓
  Permissions (roles: traveler, admin)
    ↓
Phase 3 — Core Domain
  Profiles
    ↓
  Destinations (reference data + seed script)
    ↓
  Trips
    ↓
Phase 4 — AI Planning Core
  AI Planning (design agent responsibilities on paper — Section 9)
    ↓
  Prompt Layer (prompt templates versioned in ai/prompts/)
    ↓
  LangChain (basic single-call chains wired to Groq)
    ↓
  LangGraph (multi-step orchestration graph)
    ↓
  Travel Planner Agent
    ↓
  Budget Agent
    ↓
  Recommendation Agent
    ↓
  Weather Agent
    ↓
  Packing Agent
    ↓
Phase 5 — Conversational Layer
  Memory (conversation state persistence)
    ↓
  Chat (chat app wired to ai_agents)
    ↓
  RAG (retrieval-augmented generation for destination knowledge, if needed)
    ↓
Phase 6 — Hardening
  Testing (unit → integration → API → AI-specific → load)
    ↓
  Deployment (use DockForge's existing prod config, do not modify it)
```

### 6.3 Why Every Phase Precedes The Next (Table Form)

| Phase | Must come before... | Because... |
|---|---|---|
| 0 Repo/Env | Everything | You cannot verify code runs if the platform isn't confirmed healthy first |
| 1 Django Skeleton | Auth | Apps must exist and be registered before models can live in them |
| 2 Identity | Core Domain | Every future model (`Trip`, `Profile`, etc.) has a `user` foreign key — the User model must be stable first |
| 3 Core Domain | AI Planning | Agents generate itineraries/budgets *for* a Trip — the Trip model must exist to attach AI output to |
| 4 AI Planning Core | Chat | Chat is a *conversation wrapper* around the agents — the agents must work standalone first, or debugging chat becomes impossible (can't tell if the bug is in chat or in the agent) |
| 5 Conversational | Hardening | You can't meaningfully load-test or security-test features that don't exist yet |
| 6 Hardening | (nothing — final) | Deployment is the last gate; nothing ships until tests pass |

### 6.4 Phase Completion Checklists

**Phase 0 Checklist**
- [ ] Repo cloned, DockForge present and untouched
- [ ] `.env` created from `.env.example`
- [ ] `docker compose up` succeeds
- [ ] `/health/` endpoint returns 200
- [ ] Postgres reachable via `psql`/Django shell
- [ ] Redis reachable via `redis-cli ping`

**Phase 1 Checklist**
- [ ] `apps/` directory created with `core` app first
- [ ] Each app has `apps.py` with correct `name = "apps.<name>"`
- [ ] All apps registered in `INSTALLED_APPS` in correct dependency order
- [ ] `python manage.py check` passes with zero errors

**Phase 2 Checklist**
- [ ] Custom `User` model defined BEFORE first `makemigrations` (Django rule, not just preference)
- [ ] `AUTH_USER_MODEL` set in settings before any migration exists
- [ ] Superuser created and can log into `/admin/`
- [ ] Login/registration endpoints return correct status codes for valid/invalid input

**Phase 3 Checklist**
- [ ] `Profile` auto-created via signal on `User` creation
- [ ] `Destination` seed data loaded (fixture or management command)
- [ ] `Trip` CRUD works via admin and API before AI is added

**Phase 4 Checklist**
- [ ] Each agent runs standalone via a management command or script — no Django view needed to test it
- [ ] LangGraph graph compiles and runs a full trip-planning pass on a test input
- [ ] Structured output validated against a Pydantic schema before saving to DB

**Phase 5 Checklist**
- [ ] Chat session persists across multiple messages
- [ ] Memory correctly recalls prior turns within the same session
- [ ] RAG (if implemented) returns relevant destination context, not noise

**Phase 6 Checklist**
- [ ] Coverage threshold met (see Section 11)
- [ ] Load test passes target concurrency
- [ ] Production build deployed through DockForge's existing prod compose file only

---

# SECTION 7 — Detailed Feature Development Order (Screens/Pages)

### 7.1 Page Flow Diagram

```
Landing Page
   ↓
Register ──► Login
   ↓
Dashboard (list of trips)
   ↓
Create Trip
   ↓
Trip Details (overview)
   ↓
AI Planner (input preferences, trigger generation)
   ↓
Generated Itinerary (view/edit day-by-day plan)
   ↓
Budget View
   ↓
Recommendations
   ↓
Packing List
   ↓
Saved Trips (list, revisit)
   ↓
Profile
   ↓
Settings
   ↓
Admin (staff-only)
```

### 7.2 Per-Page Requirements

| Page | Purpose | Backend Requirements | Frontend Requirements | DB Dependencies | API Dependencies |
|---|---|---|---|---|---|
| Landing | Marketing/entry point | None (static) | Static content, CTA buttons | None | None |
| Register | Create account | `accounts` app, validation, password hashing | Form + client-side validation | `User` | `POST /api/v1/auth/register/` |
| Login | Authenticate | Session or JWT issuance | Form | `User` | `POST /api/v1/auth/login/` |
| Dashboard | List user's trips | `trips` list view, pagination | Trip cards, empty state | `Trip` | `GET /api/v1/trips/` |
| Create Trip | Start new trip | `trips` create serializer, date validation | Form (dates, destination search) | `Trip`, `Destination` | `POST /api/v1/trips/`, `GET /api/v1/destinations/?search=` |
| Trip Details | Overview of one trip | `trips` detail view | Summary cards, nav to sub-sections | `Trip` | `GET /api/v1/trips/{id}/` |
| AI Planner | Collect preferences, trigger generation | `ai_agents` trigger endpoint, Celery task dispatch | Preference form, loading/progress state | `Trip`, `AgentRun` | `POST /api/v1/trips/{id}/plan/` |
| Generated Itinerary | View/edit plan | `itinerary` CRUD, ordering logic | Day tabs, drag reorder (future) | `ItineraryDay`, `ItineraryItem` | `GET/PATCH /api/v1/trips/{id}/itinerary/` |
| Budget View | Show cost breakdown | `budget` aggregation | Charts, category breakdown | `Budget`, `BudgetLineItem` | `GET /api/v1/trips/{id}/budget/` |
| Recommendations | Show AI suggestions | `recommendations` list, accept/reject | Cards with accept/dismiss actions | `Recommendation` | `GET/PATCH /api/v1/trips/{id}/recommendations/` |
| Packing List | Show packing agent output | Packing agent output storage (part of `itinerary` or its own model) | Checklist UI | `ItineraryItem`/dedicated model | `GET /api/v1/trips/{id}/packing/` |
| Saved Trips | Revisit past trips | `trips` filter by status | List/grid view | `Trip` | `GET /api/v1/trips/?status=saved` |
| Profile | View/edit preferences | `profiles` update | Form | `Profile` | `GET/PATCH /api/v1/profile/` |
| Settings | Account settings | `accounts` update, password change | Form | `User` | `PATCH /api/v1/auth/settings/` |
| Admin | Staff oversight | Django admin (built-in, minimal custom work) | Django's default admin UI | All | N/A (admin, not API) |

**Why this page order:** it mirrors the roadmap in Section 6 — you cannot build "Generated Itinerary" before "AI Planner" triggers something to generate, and you cannot build "AI Planner" before "Trip Details" exists to attach the plan to.

---

# SECTION 8 — API Planning

### 8.1 API Design Principles

- Versioned from day one: everything under `/api/v1/`.
- Resource-based URLs (nouns, not verbs): `/trips/`, not `/getTrips/`.
- AI-triggering endpoints are the one exception — they use an explicit action suffix (`/plan/`) because they don't map to plain CRUD; this is called out explicitly rather than hidden.
- All list endpoints paginated by default.
- All write endpoints validate through DRF serializers — no raw `request.data` access in views.

### 8.2 Authentication APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/register/` | Create account |
| POST | `/api/v1/auth/login/` | Obtain JWT pair |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token |
| GET/PATCH | `/api/v1/auth/settings/` | Manage account settings |

### 8.3 Trip APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET/POST | `/api/v1/trips/` | List/create trips |
| GET/PATCH/DELETE | `/api/v1/trips/{id}/` | Retrieve/update/delete a trip |
| POST | `/api/v1/trips/{id}/plan/` | Trigger AI planning (async, returns task id) |
| GET | `/api/v1/trips/{id}/status/` | Poll AI generation status |

### 8.4 Destination APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/destinations/` | List/search catalog |
| GET | `/api/v1/destinations/{id}/` | Detail |

### 8.5 Itinerary / Budget / Recommendation APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET/PATCH | `/api/v1/trips/{id}/itinerary/` | View/edit generated plan |
| GET | `/api/v1/trips/{id}/budget/` | Budget summary |
| PATCH | `/api/v1/trips/{id}/budget/line-items/{line_id}/` | Edit a single cost line |
| GET/PATCH | `/api/v1/trips/{id}/recommendations/` | List/accept/reject suggestions |

### 8.6 AI / Chat APIs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/chat/sessions/` | Start a chat session |
| GET | `/api/v1/chat/sessions/{id}/messages/` | Fetch history |
| POST | `/api/v1/chat/sessions/{id}/messages/` | Send message, get AI reply |

### 8.7 Admin APIs

Handled almost entirely via Django's built-in `/admin/` — a custom Admin API is deliberately **not** built early; it's a YAGNI (You Aren't Gonna Need It) call documented in Section 15.

### 8.8 Request/Response Flow Example — `POST /api/v1/trips/{id}/plan/`

```
Client                Django View            Celery              LangGraph            Groq
  │  POST /plan/           │                    │                    │                  │
  ├────────────────────────►                    │                    │                  │
  │                        │ validate trip owner│                    │                  │
  │                        │ create AgentRun row│                    │                  │
  │                        ├────dispatch task───►                    │                  │
  │  202 {task_id}         │                    │                    │                  │
  ◄────────────────────────┤                    │                    │                  │
  │                        │                    ├────invoke graph────►                  │
  │                        │                    │                    ├──LLM calls───────►
  │                        │                    │                    ◄──structured JSON──┤
  │                        │                    ◄──save results──────┤                  │
  │  GET /status/ (poll)   │                    │                    │                  │
  ├────────────────────────►  "completed"       │                    │                  │
  ◄────────────────────────┤                    │                    │                  │
```

**Why 202 + polling instead of waiting for the answer synchronously:** LLM multi-agent runs can take significant time; returning `202 Accepted` with a task id is the standard REST pattern for long-running operations, and it keeps the HTTP connection short-lived (better for Nginx/Gunicorn timeouts, which are part of the frozen DockForge config).

---

# SECTION 9 — AI Architecture

### 9.1 ELI10: LangChain vs LangGraph

- **LangChain** is like a recipe card: "do step A, then step B, then step C" — good for a straightforward, linear task (e.g., "summarize this destination").
- **LangGraph** is like a kitchen with multiple chefs who can hand dishes back and forth, retry a dish that came out wrong, and work some stations in parallel — good for our case, because planning a trip requires *several specialists* (planner, budget, recommendations, weather, packing) whose outputs sometimes depend on each other.

### 9.2 LangGraph Workflow for Trip Planning

```
        ┌─────────────┐
        │   START     │
        └──────┬──────┘
               ▼
     ┌──────────────────┐
     │ Travel Planner     │  (drafts day-by-day skeleton)
     │ Agent              │
     └─────────┬─────────┘
               ▼
      ┌────────┴────────┐
      ▼                 ▼
┌───────────┐     ┌──────────────┐
│ Budget    │     │ Weather      │   (run in parallel — independent of each other)
│ Agent     │     │ Agent        │
└─────┬─────┘     └──────┬───────┘
      └────────┬─────────┘
                ▼
       ┌─────────────────┐
       │ Recommendation    │  (uses itinerary + weather to suggest activities)
       │ Agent             │
       └─────────┬─────────┘
                  ▼
         ┌─────────────────┐
         │ Packing Agent     │  (uses weather + itinerary to build packing list)
         └─────────┬─────────┘
                    ▼
           ┌─────────────┐
           │   END       │  (all results merged, saved to DB)
           └─────────────┘
```

### 9.3 Agent Responsibilities

| Agent | Input | Output | Notes |
|---|---|---|---|
| Travel Planner | Trip dates, destination(s), preferences | Draft `ItineraryDay`/`ItineraryItem` structure | The "spine" all other agents build on |
| Budget Agent | Itinerary draft, budget style | `BudgetLineItem` estimates | Structured numeric output only, no prose |
| Weather Agent | Destination(s), dates | Weather summary per day | May call a real weather tool (Section 9.6) |
| Recommendation Agent | Itinerary + weather | `Recommendation` objects | Ranked, tagged by category |
| Packing Agent | Weather + itinerary + trip length | Packing checklist | Last in chain — needs everyone else's context |

### 9.4 Prompt Management

- All prompts live in `ai/prompts/`, one file per agent, versioned (`planner_v1.py`, `planner_v2.py`) so we can A/B test without breaking production.
- Prompts are never string-concatenated ad hoc inside agent code — always loaded from the prompts module. This makes prompt review possible in code review, same as reviewing SQL.

### 9.5 Memory & Conversation State

- **Short-term memory:** the current chat session's message history, stored in `ChatMessage` rows, loaded into the LangGraph state at the start of each turn.
- **Long-term memory (future):** user preference vector or summary stored on `Profile`, injected into every planning run so the AI "remembers" a user across trips, not just within one session.
- **Why not rely on the LLM's own context window alone:** context windows are finite and expensive per token; we persist memory in Postgres and only inject a relevant, summarized slice per call — this is a direct cost-control decision (see 9.9).

### 9.6 Tools & Tool Calling

Tools are plain Python functions registered with an agent, e.g. `get_weather_forecast(destination, date)`, `search_destination_pois(destination)`. The LLM decides *when* to call them; our code guarantees *what* they return is validated and safe (never pass raw LLM output into another API call unchecked — see Section 12.7 prompt injection).

### 9.7 Structured Output & Output Parsers

Every agent's final answer is forced through a **Pydantic schema** (e.g., `ItineraryDaySchema`) before it's allowed to touch the database. If the LLM's output fails schema validation, the agent retries once with an error-correction prompt, then falls back (9.8) rather than saving malformed data.

### 9.8 Fallback & Retry Strategy

```
Call LLM
   │
   ├─ Success + valid schema ──► Save
   │
   ├─ Success + invalid schema ──► Retry once with correction prompt
   │        │
   │        ├─ Now valid ──► Save
   │        └─ Still invalid ──► Fallback: mark AgentRun as "needs_review", 
   │                              surface a friendly error to user, notify ops
   │
   └─ API error/timeout ──► Retry with exponential backoff (max 3 attempts)
            │
            └─ Still failing ──► Fallback: queue for manual retry, notify user "still working on it"
```

### 9.9 Cost Optimization

- Cache identical destination-level queries (e.g., "top POIs in Kyoto") in Redis — many users asking about the same city shouldn't re-trigger the LLM every time.
- Summarize long chat histories before re-injecting them into prompts instead of sending full transcripts.
- Use the smallest model that reliably passes schema validation for a given agent (e.g., Weather Agent doesn't need the largest/most expensive model).

### 9.10 Groq API Integration

- All LLM calls go through a single wrapper in `ai/clients/groq_client.py` — no agent calls the Groq SDK directly. This is the same "single door" pattern as `ai_agents` being the only Django app allowed to touch `ai/`.
- The wrapper handles: API key loading from env (never hardcoded), timeout config, retry/backoff, and swappable provider abstraction (so switching to another provider later touches one file).

### 9.11 Context Management

- Each agent receives only the slice of state it needs (LangGraph's typed state object), not the entire conversation — reduces token cost and reduces chance of one agent's prompt leaking irrelevant info into another's reasoning.

---

# SECTION 10 — Production Architecture

*(All infrastructure below is DockForge's, described here so it's used correctly — not redesigned.)*

| Component | Role in This Project |
|---|---|
| Docker/Compose | Runs all services identically in dev and prod |
| Redis | Celery broker, cache backend, rate-limit counters |
| Celery | Runs AI agent graphs asynchronously, sends notifications |
| Nginx | Serves static files, TLS termination, reverse proxy to Gunicorn |
| Gunicorn | Runs Django WSGI workers |
| Env Variables | `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `DEBUG` — never committed, loaded via DockForge's env management |
| Logging | Application code uses Python's `logging` module with DockForge's configured handlers — never `print()` |
| Health Checks | `/health/` extended (not replaced) to also check Celery worker reachability |
| Caching | Redis used for: destination search cache, rate limiting, session cache (if session auth used) |
| Monitoring | Application emits structured logs DockForge's stack can already ingest |
| Scalability | Stateless Django workers behind Gunicorn scale horizontally; Celery workers scale independently based on AI queue depth |
| Security | See Section 12 |
| Rate Limiting | Per-user limit on `/plan/` and `/chat/` endpoints (LLM calls are the expensive resource) via Redis counters |
| Future Deployment | Same DockForge prod compose file; only new env vars and app-level settings are added, never infra changes |

---

# SECTION 11 — Testing Strategy

| Test Type | Scope | Tooling | When Run |
|---|---|---|---|
| Unit | Single function/model/serializer | `pytest` + `pytest-django` | Every commit (pre-commit + CI) |
| Integration | Multiple components together (e.g., Trip creation → Budget auto-created) | `pytest-django` with test DB | Every PR |
| API | Full request/response cycle via DRF test client | `pytest` + DRF `APIClient` | Every PR |
| AI Testing | Agent output validated against Pydantic schema using recorded/mocked LLM responses (never call real paid API in CI) | `pytest` + fixture-recorded responses | Every PR (mocked), nightly (real API smoke test) |
| Regression | Previously fixed bugs stay fixed | Named test cases per bug ticket | Every PR |
| Load Testing | Concurrent user simulation, especially around `/plan/` (AI endpoints) | Locust or k6 | Pre-release |

**Why AI testing must mock the LLM in CI:** real LLM calls are non-deterministic and cost money per call — CI must be deterministic and free to run hundreds of times a day. Real calls are reserved for a scheduled nightly "smoke test" that just confirms the provider integration itself still works.

---

# SECTION 12 — Security

| Area | Approach |
|---|---|
| Authentication | JWT (access + refresh) via DRF SimpleJWT, issued by `accounts` |
| Authorization | Object-level permissions — a user can only ever touch their own `Trip` and its children, enforced in every viewset's `get_queryset()`, never trusted from the URL alone |
| JWT | Short-lived access tokens, rotated refresh tokens, blacklist on logout |
| Permissions | Role-based: `traveler` (default), `staff` (admin access) |
| Secrets | Only via environment variables through DockForge's env management — never in code, never in git |
| Input Validation | All input via DRF serializers; never trust client-supplied IDs without ownership checks |
| Prompt Injection Protection | User input is never inserted into a prompt as raw, unescaped instruction text; user content is always wrapped in a clearly delimited "user data" section of the prompt, and agents are instructed to treat that section as data, not instructions. Tool outputs (e.g., weather API results) are similarly never treated as trusted instructions. |
| API Security | Rate limiting (Section 10), HTTPS-only (enforced at Nginx), CORS restricted to known frontend origins |
| OWASP Practices | Standard Django protections used as-is (CSRF for cookie-based flows, ORM parameterization against SQL injection, `SECURE_*` settings in prod) — none of this is reinvented, it's Django/DockForge defaults used correctly |


---

# SECTION 13 — Future Roadmap

| Future Capability | How Today's Architecture Enables It |
|---|---|
| Travel Marketplace | `bookings` app already reserved as a placeholder in Section 4; `Destination` catalog can attach partner listings |
| Hotel Booking | Extend `bookings` with a `HotelBooking` model + partner API integration behind a new tool in `ai/tools/` |
| Flight Comparison | New `flights` app + comparison agent added to the LangGraph as another node |
| AI Concierge | `chat` app already generalized as a conversation interface — extend its tool set rather than rebuilding |
| Expense Tracking | Extends `budget` app with actual (vs estimated) `BudgetLineItem` entries and receipt uploads |
| Offline Planning | Cache generated itineraries client-side; requires no backend redesign, only a service-worker/PWA layer |
| Collaborative Trips | Add `TripCollaborator` through-model (already anticipated in Section 5.9) |
| Voice Assistant | New input modality feeding into the same `chat` → `ai_agents` pipeline — speech-to-text sits in front, architecture unchanged |
| Travel Analytics | `analytics` app already scoped as read-only consumer of all other apps |
| Enterprise SaaS | Add `organizations` app (multi-tenant), `Trip.organization` FK, tenant-scoped permissions layered onto existing object-level permission pattern |

**Why this section matters even though nothing here is built now:** every "future" item above maps cleanly onto an *existing* seam in the architecture (a new app, a new agent node, a new tool). None require re-architecting core entities — that's the test of whether Sections 1–12 were designed well.

---

# SECTION 14 — Common Mistakes (And How To Avoid Them)

| Mistake | Why Beginners Make It | How This Handbook Prevents It |
|---|---|---|
| Writing code before designing models | Excitement to see something work | Section 5 forces ER design first |
| Letting AI code live inside Django views | Feels convenient short-term | Section 4.4 firewalls AI calls through `ai_agents` only |
| Calling the LLM synchronously inside a web request | Not realizing it can take 10–30s | Section 2.4 / 8.8 mandate Celery + polling |
| Trusting LLM output directly into the database | Assuming the model always returns valid JSON | Section 9.7 mandates schema validation + retry/fallback |
| Skipping tests for "AI stuff" because "it's non-deterministic" | Misunderstanding what's testable | Section 11 shows how to mock LLM calls for deterministic tests |
| Hardcoding API keys | Fastest path to "it works on my machine" | Section 12 mandates env-var-only secrets |
| Editing DockForge infra files to "fix" an app bug | Not realizing the bug is application-layer | Section 2.1 reinforces the frozen platform boundary |
| Building the `bookings`/marketplace features early because they're exciting | Chasing the fun part | Section 6 roadmap sequencing — core domain and AI core come first |
| Over-normalizing or over-denormalizing without documenting why | No decision record | Section 15 requires an ADR-style justification for every non-obvious choice |
| Not versioning prompts | Treating prompts as throwaway strings | Section 9.4 mandates a dedicated, versioned prompts module |

---

# SECTION 15 — Architecture Decisions (ADR Summary)

Each entry follows: **Decision → Why → Alternative Considered → Trade-off → Enterprise Rationale.**

### ADR-1: AI Layer as Plain Python Package, Not a Django App
- **Decision:** `ai/` lives outside `apps/`, has no models/migrations.
- **Alternative:** Make `ai_planning` a Django app with models for prompts.
- **Trade-off:** We lose Django admin editing of prompts (mitigated by keeping them in version-controlled files, arguably *better* for review/rollback).
- **Enterprise rationale:** Keeps AI logic portable and independently testable/extractable into a microservice later.

### ADR-2: Only `ai_agents` App May Import From `ai/`
- **Decision:** Single-door access pattern.
- **Alternative:** Let any app call LLM functions directly where needed.
- **Trade-off:** Slightly more indirection for simple cases.
- **Enterprise rationale:** Centralizes cost control, logging, and rate limiting for the most expensive resource in the system (LLM calls).

### ADR-3: Async AI Execution via Celery, Not Synchronous Views
- **Decision:** `/plan/` returns 202 + task id, not the finished itinerary.
- **Alternative:** Block the request until the LLM responds.
- **Trade-off:** Frontend must implement polling (or websockets later).
- **Enterprise rationale:** Protects Gunicorn worker availability under load; standard pattern for long-running operations.

### ADR-4: LangGraph Over Plain LangChain Chains
- **Decision:** Multi-agent graph with parallel/sequential dependencies.
- **Alternative:** One large single prompt doing everything.
- **Trade-off:** More moving parts to test and debug.
- **Enterprise rationale:** Single mega-prompts degrade in quality and are impossible to unit test per capability; specialized agents are independently improvable and swappable.

### ADR-5: Postgres as Source of Truth, Redis Strictly Ephemeral
- **Decision:** Nothing is stored in Redis that isn't safe to lose.
- **Alternative:** Use Redis for anything "fast," including some persistent state.
- **Trade-off:** Slightly more DB load than an all-cache approach.
- **Enterprise rationale:** Data durability guarantees must never depend on a cache; this is a standard reliability boundary.

### ADR-6: JWT Auth Over Session Auth
- **Decision:** SimpleJWT-based auth for the API.
- **Alternative:** Django session cookies.
- **Trade-off:** Slightly more client-side complexity (token storage/refresh).
- **Enterprise rationale:** Enables a fully decoupled frontend (SPA/mobile) without CSRF/cookie complications across domains.

### ADR-7: Deliberate Denormalization of `Trip.computed_budget_total`
- **Decision:** Cache a derived total on `Trip`.
- **Alternative:** Always compute it live via aggregation query.
- **Trade-off:** Requires a signal to keep it in sync; risk of drift if the signal is ever bypassed.
- **Enterprise rationale:** Dashboard read performance at scale outweighs the small sync-risk, which is mitigated with a scheduled reconciliation task.

### ADR-8: DockForge Infrastructure Is Never Modified
- **Decision:** Hard boundary, enforced by convention and code review, not just preference.
- **Alternative:** Allow application-specific infra tweaks as needed.
- **Trade-off:** Occasionally slower to adapt infra to a niche app need.
- **Enterprise rationale:** Reusable platforms only stay reusable if consumers don't fork them; this is exactly how real internal platform teams operate.

---

## Appendix — Master Checklist Before Writing Any Code

- [ ] Section 1–2 read and understood (vision + architecture)
- [ ] Folder structure (Section 3) created exactly as specified
- [ ] App creation order (Section 4) locked in
- [ ] ER diagram (Section 5) reviewed against real requirements
- [ ] Roadmap phase gates (Section 6) agreed upon
- [ ] Page-by-page requirements (Section 7) reviewed
- [ ] API contract (Section 8) drafted for Phase 1–3 endpoints
- [ ] AI architecture (Section 9) understood by whoever builds agents first
- [ ] Production/testing/security sections (10–12) acknowledged as non-negotiable defaults
- [ ] ADRs (Section 15) read — no decision here is up for silent reversal without a new ADR

**Only after every box above is checked does Phase 0 of Section 6 begin.**

---

*End of Handbook — Version 1.0*
