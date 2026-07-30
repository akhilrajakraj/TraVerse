# ADR-004: Use the Official PostgreSQL Docker Image

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

DockForge requires PostgreSQL as its primary relational database.

Since the project follows a containerized architecture, PostgreSQL must run inside a Docker container rather than being installed directly on the host operating system.

The project needed to determine whether PostgreSQL should be deployed using:

- the official PostgreSQL Docker image, or
- a custom Docker image maintained by the project.

---

# Problem Statement

There are two common approaches to running PostgreSQL in Docker.

The first approach uses the official PostgreSQL image provided by Docker Hub.

The second approach creates a custom Dockerfile that extends the official image with additional configuration or software.

The project needed to determine which approach best aligned with DockForge's goals.

---

# Options Considered

## Option 1 — Use the Official PostgreSQL Docker Image

### Example

```yaml
image: postgres:17
```

### Advantages

- Officially maintained
- Frequently updated
- Security patches are regularly released
- Simple configuration
- Minimal maintenance
- Widely used in production
- Well documented

### Disadvantages

- Less flexibility without customization

---

## Option 2 — Create a Custom PostgreSQL Docker Image

Example

```dockerfile
FROM postgres:17

COPY custom.conf /etc/postgresql/

COPY init.sql /docker-entrypoint-initdb.d/
```

### Advantages

- Full customization
- Can install PostgreSQL extensions
- Can include initialization scripts
- Can enforce organization-specific configuration

### Disadvantages

- Additional maintenance
- More complex build process
- Responsibility for image updates
- Increased project complexity

---

# Decision

DockForge will use the official PostgreSQL Docker image:

```yaml
postgres:17
```

No custom PostgreSQL Dockerfile will be created during the current development phases.

---

# Rationale

The objective of DockForge is to learn enterprise backend development while avoiding unnecessary complexity.

The official PostgreSQL image already provides:

- Production-grade reliability
- Excellent documentation
- Automatic database initialization
- Docker volume support
- Environment-variable configuration
- Strong community support

Creating a custom PostgreSQL image at this stage would provide little practical benefit while increasing maintenance effort.

The project will instead focus on application architecture rather than infrastructure customization.

---

# Future Considerations

A custom PostgreSQL image may become necessary if the project later requires:

- PostgreSQL extensions
- Custom initialization scripts
- Organization-specific configuration
- Performance tuning
- Security hardening
- Database monitoring agents

Until such requirements exist, the official image remains the preferred solution.

---

# Consequences

## Positive

- Simpler infrastructure
- Lower maintenance
- Faster onboarding for developers
- Easier upgrades
- Consistent development environment
- Industry-standard deployment approach

## Negative

- Limited customization
- Additional Dockerfile cannot be used for advanced configuration

These limitations are acceptable because they do not affect the current requirements of DockForge.

---

# Future Impact

This decision simplifies future work involving:

- Docker Compose
- Redis Integration
- Celery
- CI/CD Pipelines
- Cloud Deployment
- Kubernetes

Developers can focus on application development rather than maintaining infrastructure images.

---

# Related Documents

- Architecture: `docs/architecture/postgresql-integration.md`
- ADR-002: PostgreSQL Instead of SQLite
- ADR-003: Environment Configuration
- ADR-005: Phase 4 Retrospective

---

# Decision Summary

**Decision:** Use the official `postgres:17` Docker image.

**Reason:** It provides a secure, production-ready, and well-maintained database server while minimizing infrastructure complexity.

**Status:** Accepted