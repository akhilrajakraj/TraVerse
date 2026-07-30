# ADR-002: Use PostgreSQL Instead of SQLite

## Status

Accepted

---

## Date

July 2026

---

## Decision Makers

- Project Developer
- AI Technical Mentor

---

# Context

When a new Django project is created, it uses SQLite as the default database.

SQLite is lightweight, requires no separate server, and is excellent for learning Django fundamentals or building small personal applications.

However, DockForge is designed as an enterprise backend project whose goal is to simulate production-grade software engineering practices.

As the project grows, it will include:

- Authentication and authorization
- Multiple business modules
- REST APIs
- Concurrent users
- Redis caching
- Background task processing
- Dockerized deployment
- CI/CD pipelines

SQLite is not intended for this type of workload.

---

# Problem Statement

The project requires a database that:

- Supports multiple concurrent connections
- Provides strong ACID compliance
- Handles complex SQL queries efficiently
- Integrates well with Docker
- Is widely used in enterprise environments
- Can scale beyond local development

SQLite cannot adequately satisfy these long-term requirements.

---

# Options Considered

## Option 1 — Continue Using SQLite

### Advantages

- No installation required
- Simple configuration
- Beginner-friendly
- Fast for small projects

### Disadvantages

- Limited concurrent writes
- Not designed for production-scale systems
- Limited scalability
- Does not accurately represent enterprise architecture

---

## Option 2 — PostgreSQL

### Advantages

- Production-ready
- Excellent concurrency support
- Advanced indexing
- Robust transaction management
- Strong community support
- Industry standard for backend development
- Excellent Docker integration

### Disadvantages

- Requires a separate database server
- Slightly more complex setup than SQLite

---

# Decision

DockForge will use PostgreSQL as its primary relational database throughout the project.

SQLite will only be used during Django project creation and will be removed once PostgreSQL integration is completed.

---

# Rationale

The primary objective of DockForge is not simply to build a working application.

The objective is to learn and implement enterprise backend engineering practices.

Using PostgreSQL provides experience with:

- Database server management
- Docker networking
- Environment-based configuration
- Production-style database migrations
- Authentication management
- Persistent storage using Docker volumes

These are skills expected from modern backend engineers.

---

# Consequences

## Positive

- Enterprise-grade database
- Better portfolio quality
- Real-world development workflow
- Easier transition to production deployment
- Supports future scaling

## Negative

- Increased setup complexity
- Requires Docker during development
- More infrastructure to maintain

The additional complexity is acceptable because the educational value and production readiness significantly outweigh the disadvantages.

---

# Future Impact

This decision directly enables future phases of DockForge, including:

- Redis Integration
- Celery Background Tasks
- Docker Compose Orchestration
- REST API Development
- Production Deployment
- Horizontal Scaling

---

# Related Documents

- Architecture: `docs/architecture/postgresql-integration.md`
- ADR-003: Environment Configuration
- ADR-004: Official PostgreSQL Docker Image
- ADR-005: Phase 4 Retrospective

---

# Decision Summary

**Decision:** Adopt PostgreSQL as the primary relational database.

**Reason:** Align DockForge with enterprise backend architecture while providing practical experience with production database systems.

**Status:** Accepted