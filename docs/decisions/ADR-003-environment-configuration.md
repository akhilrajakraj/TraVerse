# ADR-003: Store Environment Configuration in `infrastructure/env`

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

Modern backend applications require different configurations depending on the environment in which they run.

Examples include:

- Local Development
- Docker Development
- Testing
- Staging
- Production

These environments often require different values for:

- Database credentials
- Secret keys
- Debug mode
- Allowed hosts
- Redis configuration
- External service credentials

The project needed a maintainable and scalable way to organize these configuration files.

---

# Problem Statement

Many Django projects place a single `.env` file in the project root directory.

Although this approach works for small projects, it becomes increasingly difficult to manage as the application grows and multiple deployment environments are introduced.

The project required a structure that clearly separates application code from infrastructure configuration.

---

# Options Considered

## Option 1 — Store `.env` in the Project Root

### Example

```
DockForge/
│
├── .env
├── backend/
├── infrastructure/
```

### Advantages

- Simple
- Common in tutorials
- Easy for beginners

### Disadvantages

- Configuration is mixed with application files.
- Difficult to organize multiple environments.
- Less suitable for enterprise deployments.

---

## Option 2 — Store Environment Files in `infrastructure/env`

### Example

```
DockForge/

├── backend/
├── infrastructure/
│   └── env/
│       ├── development.env
│       ├── production.env
│       └── testing.env
```

### Advantages

- Infrastructure is organized separately from application code.
- Easy to manage multiple environments.
- Scales well as the project grows.
- Better reflects enterprise repository organization.

### Disadvantages

- Slightly more setup is required.
- Developers must explicitly load the correct environment file.

---

# Decision

DockForge will store all environment configuration files inside:

```
infrastructure/env/
```

instead of placing a `.env` file in the repository root.

---

# Rationale

The primary goal of DockForge is to follow enterprise backend engineering practices.

Separating infrastructure configuration from application code provides several long-term benefits:

- Cleaner repository organization
- Easier deployment automation
- Better support for multiple environments
- Reduced risk of configuration confusion
- Improved maintainability

This approach also aligns well with future Docker Compose, CI/CD, and cloud deployment workflows.

---

# Environment Strategy

The project currently includes:

```
development.env
```

Future phases may introduce:

```
production.env
testing.env
```

Each file represents a specific deployment environment and contains only the configuration relevant to that environment.

---

# Consequences

## Positive

- Cleaner project organization
- Easier infrastructure management
- Better scalability
- Simplified deployment workflows
- Enterprise-style repository structure

## Negative

- Slightly more complex than using a root `.env`
- Requires developers to understand environment loading

The additional complexity is acceptable because it improves maintainability and better reflects production software engineering practices.

---

# Future Impact

This decision supports future phases including:

- Redis Integration
- Docker Compose
- Celery
- CI/CD Pipelines
- Cloud Deployment
- Kubernetes
- Secret Management

---

# Related Documents

- Architecture: `docs/architecture/postgresql-integration.md`
- ADR-002: PostgreSQL Instead of SQLite
- ADR-004: Official PostgreSQL Docker Image
- ADR-005: Phase 4 Retrospective

---

# Decision Summary

**Decision:** Store environment configuration inside `infrastructure/env/`.

**Reason:** Separate infrastructure configuration from application code and prepare DockForge for enterprise deployment workflows.

**Status:** Accepted