# ADR-010: Health-Based Service Startup Dependencies

**Status:** Accepted

**Date:** Phase 07

**Decision Type:** Infrastructure

---

# Context

Container startup order plays a critical role in the stability of a multi-service application.

Docker starts containers quickly, but a running container does not necessarily indicate that the application inside the container is ready to process requests.

For example, a Django container may still be:

- Applying application initialization
- Establishing database connectivity
- Initializing the cache backend
- Completing startup tasks

If another service begins communicating with Django before these steps are complete, requests may fail even though the container is technically running.

DockForge required a startup strategy that reflects application readiness rather than container state.

---

# Problem Statement

Traditional startup dependencies ensure that containers start in a specific order, but they do not verify that a dependent application is fully operational.

Example:

```
PostgreSQL
      │
      ▼
Django Container Started
      │
      ▼
Nginx Starts Routing Traffic
```

Although the Django container is running, the application may still be initializing.

This can lead to:

- HTTP 502 Bad Gateway responses
- Connection failures
- Failed health checks
- Unnecessary restart cycles
- Poor developer experience during startup

A more reliable startup mechanism was required.

---

# Decision

DockForge adopts **health-based startup dependencies**.

Instead of depending only on container startup, dependent services wait until the Django application reports a healthy status through the `/health/` endpoint.

Docker Compose uses health checks together with dependency conditions to determine when the application is ready.

This ensures that infrastructure startup is driven by application readiness rather than process execution.

---

# Architecture

```
PostgreSQL
      │
      ▼
Redis
      │
      ▼
Django Container
      │
      ▼
Application Startup
      │
      ▼
/health/
Returns Healthy
      │
      ▼
Docker Marks Container Healthy
      │
      ▼
Nginx Begins Routing Requests
```

Only after the health check succeeds does the backend become available to dependent services.

---

# Alternatives Considered

## Option 1 — Container Startup Only

Advantages:

- Simple configuration
- Minimal setup

Disadvantages:

- Does not verify application readiness
- Increased risk of startup failures
- Dependent services may fail during initialization

Result:

Rejected.

---

## Option 2 — Manual Startup Delays

Advantages:

- Easy to implement

Disadvantages:

- Startup timing is unpredictable
- Different systems initialize at different speeds
- Fixed delays may be too short or unnecessarily long

Result:

Rejected.

---

## Option 3 — Health-Based Dependencies

Advantages:

- Startup based on application readiness
- More reliable deployments
- Better fault isolation
- Cleaner service coordination
- Industry-standard approach for containerized systems

Disadvantages:

- Requires a health endpoint
- Slightly more infrastructure configuration

Result:

Accepted.

---

# Consequences

Positive outcomes include:

- Improved startup reliability
- Fewer transient startup failures
- Better coordination between services
- More predictable deployments
- Easier debugging during development

Trade-offs include:

- Additional health check implementation
- Slight increase in infrastructure complexity

These trade-offs are justified by the improvements in reliability and operational consistency.

---

# Impact

This decision affects:

- Docker Compose configuration
- Django health endpoint
- Nginx startup behavior
- Service dependency management
- Infrastructure documentation

It also establishes a deployment pattern that can be extended to future services introduced into the DockForge ecosystem.

---

# Future Considerations

Future infrastructure enhancements may expand this startup strategy to additional services.

Possible improvements include:

- Background worker health verification
- Scheduled task readiness checks
- External dependency validation
- Service-specific readiness endpoints
- Kubernetes readiness and liveness probes

These enhancements can build upon the same health-first design established in Phase 07.

---

# Summary

DockForge adopts a health-first startup strategy to ensure that services interact only with applications that are fully operational.

By combining Docker health checks with application-level readiness verification, the infrastructure becomes more reliable, more predictable, and better aligned with modern deployment practices.

This decision reinforces DockForge's goal of providing a reusable, production-oriented backend foundation rather than simply orchestrating running containers.