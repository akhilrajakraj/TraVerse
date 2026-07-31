# Chapter 03 — Core App: Shared Foundations

## Chapter Overview

Chapter 03 establishes the foundational infrastructure shared by every application within the TraVerse platform.

Unlike feature-oriented applications such as `accounts`, `trips`, or `planner`, the `core` application exists solely to provide reusable building blocks. It contains no business-specific logic and introduces no concrete database tables. Instead, it defines the common abstractions, utilities, permissions, exception hierarchy, and model managers that every future application will depend upon.

This chapter marks the transition from project scaffolding to application architecture. While Chapter 02 focused on constructing the Django application structure, Chapter 03 introduces the first reusable software components that form the backbone of the platform.

---

# Objectives

The primary objectives of this chapter are:

- Establish reusable abstract base models.
- Centralize timestamp handling.
- Provide optional UUID primary key support.
- Introduce soft-delete infrastructure.
- Create a standardized application exception hierarchy.
- Build reusable DRF permission classes.
- Introduce shared serializer mixins.
- Implement reusable model managers.
- Establish the project's testing convention.
- Validate that shared infrastructure behaves correctly before any domain models are introduced.

---

# Scope

This chapter intentionally avoids implementing business functionality.

No application-specific models are created.

No API endpoints are exposed.

No serializers are implemented.

No authentication logic is introduced.

No database schema is expanded through concrete models.

Instead, this chapter focuses entirely on reusable infrastructure that future chapters will consume.

---

# Architectural Role of the Core Application

The `core` application occupies the lowest level of the project's dependency graph.

Every future application may import components from `core`.

The `core` application itself must never depend on domain applications.

The dependency direction therefore becomes:

```text
               apps.core
                    ▲
                    │
    ┌───────────────┼────────────────┐
    │               │                │
accounts        planner          trips
    │               │                │
notifications   bookings      analytics
```

This one-directional dependency model prevents circular imports and keeps shared infrastructure isolated from business logic.

---

# Components Introduced

The chapter introduces the following reusable infrastructure.

| Component | Purpose |
|-----------|---------|
| TimeStampedModel | Shared creation and modification timestamps |
| UUIDPrimaryKeyModel | UUID primary key abstraction |
| SoftDeleteModel | Soft deletion support |
| ApplicationError | Base application exception |
| BusinessRuleViolation | Business rule exception |
| ResourceNotOwned | Ownership violation exception |
| ExternalServiceError | External dependency failure |
| IsOwner | Generic object ownership permission |
| IsStaffOrReadOnly | Shared read/write permission |
| RequestUserContextMixin | Serializer convenience mixin |
| SoftDeleteManager | Default manager excluding deleted records |

---

# Testing Strategy

Unlike previous chapters, Chapter 03 introduces structured unit testing.

Instead of relying on Django's default `tests.py`, the project adopts a package-based testing layout.

```text
apps/core/tests/
├── __init__.py
├── test_models.py
├── test_exceptions.py
└── test_permissions.py
```

This testing convention becomes the standard for every application created throughout the remainder of the project.

---

# Validation Strategy

Every implementation phase was validated immediately after completion.

Validation included:

- Django configuration checks.
- Abstract model verification.
- Permission import verification.
- Individual unit test execution.
- Full application test execution.

Incremental validation ensured defects were isolated to individual implementation phases rather than discovered after multiple components had been completed.

---

# Deliverables

By the conclusion of Chapter 03, the following artifacts were completed:

- Shared abstract base models.
- Shared exception hierarchy.
- Shared DRF permissions.
- Shared serializer mixins.
- Shared model managers.
- Structured test package.
- Thirteen passing unit tests.
- Successful Django configuration validation.

---

# Outcome

Chapter 03 transforms the `core` application from an empty scaffold into the foundational engineering layer of TraVerse.

Every subsequent chapter will build upon the abstractions established here rather than reimplementing shared functionality.

This establishes consistency, reduces duplication, and creates a maintainable foundation for the remainder of the platform.

---

# Future Consumers

The reusable infrastructure introduced in this chapter forms the foundation for every domain application that follows.

Beginning with Chapter 04, applications will inherit these shared components instead of redefining common functionality.

Examples include:

| Future Chapter | Shared Components Used |
|----------------|------------------------|
| Chapter 04 — Accounts | `TimeStampedModel`, `ApplicationError` |
| Chapter 05 — Profiles | `TimeStampedModel`, `IsOwner` |
| Chapter 06 — Destinations | `TimeStampedModel`, `IsStaffOrReadOnly` |
| Chapter 07 — Trips | `TimeStampedModel`, `UUIDPrimaryKeyModel`, `SoftDeleteModel`, `IsOwner` |
| Later Chapters | Exception hierarchy, serializer mixins, shared managers |

No future application should duplicate timestamp handling, ownership permissions, shared exceptions, or soft-delete behavior.

The `core` application remains the single source of truth for reusable infrastructure throughout the TraVerse platform.