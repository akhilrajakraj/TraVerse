# ADR-005: Use Redis as the Primary Cache for DockForge

**Status:** Accepted

**Date:** 2026-07-26

**Project:** DockForge

---

# Context

DockForge initially relied solely on PostgreSQL for data storage and retrieval.

Every request from the application required Django to communicate directly with PostgreSQL.

The architecture was:

```text
Browser
    │
    ▼
Django
    │
    ▼
PostgreSQL
```

Although PostgreSQL is an excellent relational database, repeatedly executing identical queries for frequently requested information is inefficient.

As DockForge grows, repeated database queries can increase:

- Database workload
- CPU utilization
- Disk I/O
- Response time
- Infrastructure costs

To improve application performance and prepare the project for future enterprise features, a caching solution was required.

---

# Problem Statement

The application lacked a dedicated caching layer.

Without caching:

- Every request reaches PostgreSQL.
- Frequently requested information is regenerated repeatedly.
- Database resources are used even when data has not changed.
- Response time increases as traffic grows.

The project required a solution that could temporarily store frequently requested data while leaving PostgreSQL as the permanent source of truth.

---

# Decision

DockForge will use **Redis** as its primary caching solution.

Redis will function as an **in-memory cache** positioned between Django and PostgreSQL.

The application architecture becomes:

```text
Browser
    │
    ▼
Django
    │
    ▼
Django Cache Framework
    │
    ▼
Redis
    │
(Cache Miss Only)
    ▼
PostgreSQL
```

Redis will not replace PostgreSQL.

Instead, Redis will cache frequently requested information and reduce unnecessary database queries.

---

# Why Redis?

Several caching solutions exist.

Redis was selected because it provides:

- Extremely fast in-memory storage
- Mature ecosystem
- Excellent Django support
- Simple Docker deployment
- Production readiness
- Broad industry adoption

Redis integrates directly with Django through the `django-redis` package, allowing the application to use Django's native Cache Framework.

---

# Alternatives Considered

## Option 1 — No Cache

Architecture:

```text
Browser

↓

Django

↓

PostgreSQL
```

### Advantages

- Simpler architecture
- No additional infrastructure
- Fewer moving parts

### Disadvantages

- Every request queries PostgreSQL
- Poor scalability
- Increased database workload
- Higher response times

Decision:

Rejected.

The long-term performance cost outweighs the simplicity.

---

## Option 2 — Local Memory Cache

Django provides a built-in local memory cache.

Advantages:

- No external service
- Easy configuration

Disadvantages:

- Cache exists only inside one Django process
- Data is lost when the application restarts
- Cannot be shared between multiple application servers

Decision:

Rejected.

Not suitable for enterprise deployments.

---

## Option 3 — Database Cache

Store cached information inside PostgreSQL.

Advantages:

- No additional infrastructure

Disadvantages:

- Cached data still requires database queries
- Increases database workload
- Provides limited performance improvement

Decision:

Rejected.

Caching should reduce database workload rather than increase it.

---

## Option 4 — Redis Cache

Advantages:

- Extremely fast
- Dedicated cache server
- Shared across application instances
- Excellent Django integration
- Docker friendly
- Enterprise standard

Disadvantages:

- Requires an additional infrastructure service
- Cached data is temporary

Decision:

Accepted.

---

# Consequences

## Positive

- Faster response times
- Reduced PostgreSQL workload
- Better scalability
- Foundation for future Redis features
- Enterprise-grade architecture
- Cleaner separation of responsibilities

---

## Negative

- Additional service to maintain
- Additional Docker container
- More infrastructure configuration

These disadvantages are acceptable considering the performance improvements Redis provides.

---

# Architectural Impact

Before Redis:

```text
Browser
    │
    ▼
Django
    │
    ▼
PostgreSQL
```

After Redis:

```text
Browser
    │
    ▼
Django
    │
    ▼
Redis
    │
(Cache Miss)
    ▼
PostgreSQL
```

Redis becomes the application's first lookup location.

PostgreSQL remains the permanent data store.

---

# Implementation Summary

Redis was integrated using:

- Docker
- Official Redis Docker image
- Django Cache Framework
- django-redis backend
- Environment variables
- Redis cache verification
- HTTP cache demonstration endpoint

The integration was verified through:

- Docker container verification
- Django configuration checks
- Cache write operations
- Cache read operations
- HTTP endpoint testing

---

# Future Considerations

Redis will initially be used only for caching.

Future DockForge phases may extend Redis usage to support:

- User sessions
- Celery task queues
- Rate limiting
- OTP storage
- Temporary authentication tokens
- Notification systems
- Real-time event processing

The current implementation establishes the foundation for these future capabilities.

---

# Final Decision

Redis has been adopted as the primary caching solution for DockForge.

PostgreSQL remains the source of truth.

Redis serves as the application's high-performance caching layer.

This decision improves performance, prepares the project for future scalability, and aligns DockForge with modern enterprise backend architecture.