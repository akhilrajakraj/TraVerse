<div align="center">

# 🌍 TraVerse

### The intelligent workspace for planning better journeys

**AI-assisted travel planning · Itineraries · Recommendations · Budget · Weather · Trip intelligence**

<p>
  <a href="https://github.com/akhilrajakraj/TraVerse/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/akhilrajakraj/TraVerse/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI status"></a>
  <img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 5.2">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=111827" alt="React 19">
  <img src="https://img.shields.io/badge/TypeScript-7-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript 7">
  <img src="https://img.shields.io/badge/PostgreSQL-17-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 17">
  <img src="https://img.shields.io/badge/Redis-8-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis 8">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose">
</p>

<p>
  <a href="https://github.com/akhilrajakraj/TraVerse">Repository</a> ·
  <a href="https://github.com/akhilrajakraj/TraVerse/tree/main/docs">Documentation</a> ·
  <a href="https://github.com/akhilrajakraj/TraVerse/pulls">Pull Requests</a>
</p>

</div>

---

## 🧭 What is TraVerse?

TraVerse is a **full-stack intelligent travel-planning platform** built around one idea: travel planning should feel like working with a capable trip workspace, not stitching together a dozen disconnected tools.

Instead of treating AI as a decorative chatbot, TraVerse places AI inside an application workflow where generated results become **reviewable, observable, and connected to real trip data**.

A trip can evolve from a destination idea into a structured plan with:

- 🤖 AI-assisted itinerary planning
- 🗺️ Destination discovery and recommendations
- 📅 Day-by-day itinerary management
- 🌦️ Weather information attached to itinerary days
- 💰 Budget planning and line-item tracking
- 🧠 AI recommendation review and lifecycle decisions
- 👤 User profiles and trip ownership
- ⚡ Asynchronous AI execution through Celery and Redis
- 🐘 PostgreSQL-backed persistence
- 🐳 Dockerized development infrastructure

**TraVerse is currently under active development.** The foundation is already substantial, while additional travel domains and frontend chapters continue to be implemented against the existing backend contracts.

---

## ✨ Why TraVerse is different

### AI that participates in the product workflow

The AI layer is not isolated from the application. TraVerse contains dedicated agents and orchestration for areas such as travel planning, recommendations, budget assistance, packing assistance, weather, and chat, with shared context and memory infrastructure.

### Backend-authoritative by design

Frontend features are implemented against the **actual Django API contracts** rather than invented mock interfaces. This keeps the UI aligned with serializers, lifecycle states, permissions, and persisted domain data.

### Asynchronous by design

Long-running AI work is handled through **Celery + Redis**, while the frontend observes the authoritative `AgentRun` lifecycle instead of pretending that AI generation is an instantaneous browser operation.

### Built to be maintainable

TraVerse is organized as a modular Django application with feature-oriented React code, typed API boundaries, TanStack Query data fetching, focused tests, Docker infrastructure, and reconciliation documentation for major implementation chapters.

---

# 🚀 Current Platform

The following represents the **implemented platform surface**, not a wish-list of future features.

| Area | Current capability |
|---|---|
| 🔐 Accounts | Authentication and user account workflows |
| 👤 Profiles | User profile surface and profile data |
| 🧳 Trips | Trip creation, trip listing, trip detail workflow, destinations and trip ownership |
| 📍 Destinations | Destination catalog and search/discovery UI |
| 📅 Itinerary | Day-by-day itinerary viewing and activity creation |
| 🌦️ Weather | Weather presentation attached to itinerary days |
| 💰 Budget | Computed totals, planned totals, categories, line items and add-item workflow |
| ⭐ Recommendations | Destination recommendations with lifecycle filtering and accept/reject decisions |
| 🤖 AI Planner | Triggering, asynchronous status polling, retry/review states and generated-plan review |
| 🧠 AI Recommendation Review | AI-generated recommendations ordered by backend score with explicit review actions |
| 🐳 Infrastructure | Docker Compose, PostgreSQL, Redis, Django, Celery and Nginx |
| 🧪 Quality | Backend Django test suite, frontend Vitest tests and CI type-check/build verification |
| 📚 Engineering Docs | Architecture, API, decisions and chapter-by-chapter reconciliation documentation |

> **Important:** A directory or backend app existing in the repository does not automatically mean its end-user workflow is complete. This README intentionally distinguishes the current implemented product surface from the broader architecture and future roadmap.

---

# 🧠 AI Architecture

TraVerse's AI layer is organized as a real application subsystem rather than a single prompt call.

```text
                        ┌─────────────────────┐
                        │   TraVerse Frontend  │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Django REST API   │
                        └──────────┬──────────┘
                                   │
                         asynchronous execution
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   Celery + Redis    │
                        └──────────┬──────────┘
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │       AI Orchestration     │
                    │      / LangGraph layer     │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
   Travel Planner         Recommendation Agent       Weather Agent
   Budget Agent            Packing Agent              Chat Agent
          │                       │                        │
          └───────────────────────┼────────────────────────┘
                                  ▼
                        ┌─────────────────────┐
                        │ Shared AI Context & │
                        │ Memory / Schemas    │
                        └──────────┬──────────┘
                                   ▼
                        ┌─────────────────────┐
                        │ Groq + Pydantic     │
                        │ Structured Outputs  │
                        └─────────────────────┘
```

The repository currently contains dedicated AI agents for travel planning, recommendations, budget, packing, weather and chat, alongside shared schemas, context, graphs, memory and a Groq client.

The design goal is deliberate separation between:

**product state → AI orchestration → structured output → persistence → frontend review**

That boundary is particularly important for generated itineraries: the application does not treat an AI response as successful merely because the model returned text. The result must satisfy the application's structured contract before it becomes authoritative trip data.

---

# 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                         TraVerse                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  React 19 + TypeScript + TanStack Query + React Router      │
│                         │                                   │
│                         ▼                                   │
│                 Django REST Framework                        │
│                         │                                   │
│          ┌──────────────┼───────────────┐                   │
│          ▼              ▼               ▼                   │
│     Domain Apps      AI Agents       Background Jobs        │
│          │              │               │                   │
│          │              ▼               │                   │
│          │       LangGraph / Groq       │                   │
│          │                              │                   │
│          └──────────────┬───────────────┘                   │
│                         ▼                                   │
│                    PostgreSQL                              │
│                         ▲                                   │
│                         │                                   │
│                       Redis                                 │
│                         ▲                                   │
│                         │                                   │
│                      Celery                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Backend domain organization

The backend is organized into dedicated Django applications covering domains including:

`accounts` · `profiles` · `trips` · `destinations` · `itinerary` · `recommendations` · `budget` · `planner` · `ai_agents` · `documents` · `notifications` · `payments` · `bookings` · `analytics` · `chat` · `core`

This separation allows each domain to evolve without collapsing the project into a single monolithic application module.

### Frontend organization

The frontend follows a feature-oriented structure with areas including:

`auth` · `home` · `trips` · `destinations` · `itinerary` · `budget` · `recommendations` · `ai-planner` · `profile` · `theme` · `workspace` · `bookings` · `chat` · `documents` · `notifications`

Shared UI and API infrastructure sit outside individual feature domains so feature code can reuse consistent application primitives.

---

# 🛠️ Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | React 19 | User interface |
| Frontend Language | TypeScript 7 | Static typing and safer API contracts |
| Frontend Routing | React Router 7 | Application navigation |
| Server State | TanStack Query 5 | Fetching, caching, polling and mutation state |
| Frontend Build | Vite 8 | Development and production builds |
| Frontend Testing | Vitest + Testing Library | Component and API-boundary regression coverage |
| Backend | Django 5.2 | Application framework |
| API | Django REST Framework 3.16 | REST API layer |
| Authentication | Simple JWT | Token-based authentication |
| Database | PostgreSQL 17 | Persistent relational data |
| Cache / Broker | Redis 8 | Caching and asynchronous job infrastructure |
| Task Queue | Celery 5.5 | Background AI and application jobs |
| AI Orchestration | LangGraph | Structured agent workflows |
| AI Provider | Groq | Model inference |
| Validation | Pydantic 2 | Structured AI contracts |
| Web Server | Gunicorn | Django application server |
| Reverse Proxy | Nginx | HTTP entry point / proxy layer |
| Infrastructure | Docker Compose | Reproducible local environment |
| CI | GitHub Actions | Automated backend checks and frontend build verification |

The backend runtime image currently uses Python 3.10, while CI runs the backend test suite on Python 3.11. The frontend declares Node.js `>=20.19.0` and CI pins Node.js `20.19.0`.

---

# 📁 Repository Structure

```text
TraVerse/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── nightly-smoke.yml
│
├── backend/
│   ├── ai/
│   │   ├── agents/
│   │   ├── clients/
│   │   ├── context/
│   │   ├── graphs/
│   │   └── memory/
│   │
│   ├── apps/
│   │   ├── accounts/
│   │   ├── ai_agents/
│   │   ├── analytics/
│   │   ├── bookings/
│   │   ├── budget/
│   │   ├── chat/
│   │   ├── core/
│   │   ├── destinations/
│   │   ├── documents/
│   │   ├── itinerary/
│   │   ├── notifications/
│   │   ├── payments/
│   │   ├── planner/
│   │   ├── profiles/
│   │   └── ...
│   │
│   ├── config/
│   ├── requirements/
│   ├── scripts/
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── hooks/
│   │   └── lib/
│   ├── scripts/
│   ├── package.json
│   └── vite.config.*
│
├── infrastructure/
│   ├── compose/
│   ├── docker/
│   └── env/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── decisions/
│   └── implementation/
│
├── tests/
├── .env.example
├── LICENSE
└── README.md
```

---

# ⚡ Quick Start

## 1. Clone the repository

```bash
git clone https://github.com/akhilrajakraj/TraVerse.git
cd TraVerse
```

## 2. Configure development environment

Create the development environment file from the repository's example configuration and provide the required local values, including the database and AI configuration used by your environment.

> Do not commit real secrets. The repository provides `.env.example` as the safe configuration template.

## 3. Start the Docker development stack

From the repository root:

```bash
docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/compose/docker-compose.dev.yml up --build
```

The development composition starts the core platform services and preserves PostgreSQL data through the named `postgres_data` volume.

### Core services

| Service | Purpose |
|---|---|
| `django` | Django development server / REST API |
| `celery` | Background task worker |
| `postgres` | Persistent relational database |
| `redis` | Cache and Celery infrastructure |
| `nginx` | HTTP reverse proxy |

## 4. Verify the backend

The Django service exposes a health endpoint at:

```text
/health/
```

The repository also contains platform verification and application test tooling under `backend/scripts/` and the Django test suite.

## 5. Run the frontend

From `frontend/`:

```bash
npm install
npm run dev
```

The frontend package also provides:

```bash
npm test
npm run build
npm run verify:api
```

These correspond to the repository's current frontend test, production-build and API verification workflows.

---

# 🧪 Quality & Verification

TraVerse treats verification as part of implementation, not an afterthought.

### Backend CI

GitHub Actions currently verifies:

- Django system checks
- migration consistency
- the full Django test suite

with PostgreSQL 17 and Redis 8 service containers.

### Frontend CI

The frontend CI job currently verifies the TypeScript/build contract with:

```text
npm run build
```

The local frontend suite is available through:

```text
npm test
```

### Development discipline

Major feature chapters follow a reconciliation-first workflow:

```text
Audit current backend
        ↓
Verify actual API contract
        ↓
Map frontend architecture
        ↓
Implement smallest safe change
        ↓
Add regression tests
        ↓
Document reconciliation decisions
        ↓
Run verification
        ↓
Review / merge
```

This is intentional: **the existing system is the source of truth.** New UI should adapt to the backend contract rather than forcing the backend to match assumptions made by a frontend mock.

---

# 📚 Documentation

The `docs/` tree contains the engineering record of TraVerse.

```text
docs/
├── architecture/
├── api/
├── decisions/
└── implementation/
```

Implementation chapters document how individual frontend/backend capabilities were reconciled with the existing architecture. The frontend roadmap reference tracks the sequence and boundaries of the remaining UI work.

For contributors, the documentation is more than reference material—it is part of the project's architectural memory.

---

# 🗺️ Development Roadmap

The current frontend implementation has progressed through **Chapter 15**, with the recommendation review UI merged into `main`. The persistent frontend roadmap now points toward **Chapter 16 — Packing List UI**.

The roadmap is intentionally incremental. Each chapter is expected to:

- audit the current backend first;
- preserve existing contracts;
- reuse established frontend patterns;
- avoid unnecessary backend modifications;
- include focused regression coverage;
- update reconciliation documentation;
- pass the repository's verification gates before merge.

### Near-term direction

- 🧳 Packing-list experience backed by the existing packing domain
- 🧾 Additional trip-workspace capabilities
- 🔔 Notifications and connected travel workflows
- 📄 Documents and travel artifacts
- 💬 Chat and conversational travel assistance
- 📊 Analytics and richer trip intelligence
- 🏨 Booking/payment workflows as their respective backend contracts mature

> These are development directions, not claims that every listed domain is currently complete in the end-user UI.

---

# 🔐 Engineering Principles

TraVerse is built around a small set of principles that guide every feature chapter:

### 1. Backend contracts are authoritative

Serializers, endpoints, lifecycle states, permissions and persisted domain models are inspected before frontend implementation.

### 2. AI output must be trustworthy before it becomes product state

Structured AI output is validated against application schemas. Failed generation is represented as a recoverable state rather than silently treated as a successful itinerary.

### 3. Async work stays asynchronous

AI planning runs through background infrastructure. The frontend observes the backend's run state rather than implementing its own fake generation lifecycle.

### 4. Minimal surface-area changes

If an existing backend already supports a feature, the frontend consumes it. Backend changes are made only when the existing contract genuinely cannot support the required behavior.

### 5. Tests protect contracts

API boundaries, component behavior, lifecycle states and edge cases receive regression coverage as features evolve.

### 6. Documentation preserves architectural intent

Important implementation decisions are recorded so future chapters can extend the system without repeatedly rediscovering why earlier choices were made.

---

# 🤝 Contributing

Contributions are welcome, but TraVerse values **architectural consistency over isolated feature additions**.

A strong contribution should:

1. Understand the existing domain and architecture.
2. Inspect the current backend contract before changing the frontend.
3. Reuse existing API, query, UI and state-management patterns.
4. Avoid introducing duplicate infrastructure or unsupported abstractions.
5. Add regression tests for changed behavior.
6. Update relevant documentation when the architecture or workflow changes.
7. Verify the build and applicable test suites before opening a pull request.

For substantial changes, a pull request should clearly explain the problem, implementation boundary, verification performed, and any deliberate non-changes.

---

# 📄 License

TraVerse is distributed under the **MIT License**. See [`LICENSE`](./LICENSE) for the complete license text.

---

<div align="center">

## 🌍 Plan with intelligence. Build with discipline. Travel with confidence.

**TraVerse**

*An evolving full-stack travel intelligence platform.*

<br>

⭐ If TraVerse is useful or interesting to you, consider starring the repository.

</div>
