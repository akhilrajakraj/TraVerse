# Chapter 03 — Implementation

## Introduction

This document records the implementation process of the shared `core` application.

Unlike feature-oriented applications, the `core` application contains reusable infrastructure that is consumed throughout the TraVerse platform. The objective of this chapter was to establish a clean architectural foundation before introducing domain-specific applications.

The implementation was completed incrementally, with each phase validated independently before proceeding to the next.

---

# Phase 1 — Abstract Base Models

## Objective

Create reusable abstract models that eliminate duplication across future applications.

## Components Implemented

### TimeStampedModel

Provides automatic creation and modification timestamps.

```python
created_at
updated_at
```

Purpose:

- Automatic audit information
- Consistent timestamp handling
- Reduced code duplication

---

### UUIDPrimaryKeyModel

Provides UUID-based primary keys.

```python
id = models.UUIDField(...)
```

Purpose:

- Globally unique identifiers
- Improved security compared to sequential IDs
- Better support for distributed systems

---

### SoftDeleteModel

Introduces logical deletion.

```python
is_deleted
deleted_at
```

Purpose:

- Preserve historical records
- Support audit requirements
- Prevent accidental permanent deletion

---

## Architectural Decision

All models were declared abstract.

```python
class Meta:
    abstract = True
```

This prevents Django from creating unnecessary database tables while allowing inheritance.

---

# Phase 2 — Exception Hierarchy

## Objective

Centralize application-level exception handling.

## Components

### ApplicationError

Base exception class.

Acts as the parent of all custom application exceptions.

---

### BusinessRuleViolation

Represents violations of business rules.

Example:

- Duplicate booking
- Invalid reservation state

---

### ResourceNotOwned

Raised when a user attempts to access a resource they do not own.

Example:

- Editing another user's itinerary
- Deleting another user's trip

---

### ExternalServiceError

Represents failures originating from external systems.

Example:

- Payment gateway failure
- Email service outage
- Third-party API timeout

---

## Architectural Benefits

Centralized exception handling enables:

- Consistent API responses
- Easier logging
- Simplified debugging
- Cleaner service-layer code

---

# Phase 3 — Permission Classes

## Objective

Provide reusable DRF permission classes.

## Components

### IsOwner

Allows object access only to the resource owner.

Comparison:

```python
request.user.id == obj.user_id
```

This permission will be reused throughout the platform.

---

### IsStaffOrReadOnly

Allows unrestricted read operations while restricting write operations to staff users.

Safe methods:

- GET
- HEAD
- OPTIONS

Write methods require:

```python
request.user.is_staff
```

---

## Benefits

- Eliminates duplicated permission logic.
- Encourages consistent authorization.
- Simplifies view implementation.

---

# Phase 4 — Serializer Mixins

## Objective

Reduce repetitive serializer code.

## Component

### RequestUserContextMixin

Provides convenient access to the authenticated request user through serializer context.

Benefits include:

- Cleaner serializer implementations
- Reduced boilerplate
- Standardized access pattern

---

# Phase 5 — Model Managers

## Objective

Provide reusable managers for soft-delete functionality.

## Component

### SoftDeleteManager

Filters deleted records automatically.

Instead of:

```python
Model.objects.filter(is_deleted=False)
```

applications simply use:

```python
Model.objects.all()
```

This centralizes filtering behavior and prevents accidental exposure of deleted records.

---

# Phase 6 — Testing Infrastructure

The default Django testing layout:

```text
tests.py
```

was replaced with a structured package.

```text
tests/
├── __init__.py
├── test_models.py
├── test_exceptions.py
└── test_permissions.py
```

This layout improves scalability as each application grows.

---

# Phase 7 — Model Tests

Verified that all shared base models remain abstract.

Tests covered:

- TimeStampedModel
- UUIDPrimaryKeyModel
- SoftDeleteModel

Result:

```
3 tests passed
```

---

# Phase 8 — Exception Tests

Verified:

- Default messages
- Default error codes
- Custom initialization
- Correct inheritance hierarchy

Result:

```
5 tests passed
```

---

# Phase 9 — Permission Tests

Verified:

### IsOwner

- Owner allowed
- Non-owner denied

### IsStaffOrReadOnly

- Read operations allowed
- Staff write operations allowed
- Non-staff write operations denied

Result:

```
5 tests passed
```

---

# Dependency Introduced

During implementation, Django REST Framework was added to the project.

Requirement:

```
djangorestframework==3.16.1
```

Configuration:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
]
```

This prepares the project for API development in subsequent chapters.

---

# Validation

Validation was performed after every implementation phase.

Commands executed included:

```bash
python manage.py check
```

```bash
python manage.py test apps.core.tests.test_models
```

```bash
python manage.py test apps.core.tests.test_exceptions
```

```bash
python manage.py test apps.core.tests.test_permissions
```

```bash
python manage.py test apps.core
```

All validation completed successfully.

---

# Final Result

At the conclusion of Chapter 03, the `core` application provides reusable infrastructure for every future application within TraVerse.

Future chapters will inherit these shared components rather than reimplementing common functionality, ensuring consistency, reducing duplication, and improving long-term maintainability.

---

# Why Django REST Framework Was Introduced in This Chapter

Although API endpoints are not implemented until later chapters, Django REST Framework was intentionally introduced during the implementation of the `core` application.

The shared permission classes (`IsOwner` and `IsStaffOrReadOnly`) inherit from DRF's `BasePermission`, making DRF a foundational dependency rather than an application-specific one.

Introducing DRF at this stage provides several benefits:

- permission classes can be validated immediately,
- future applications inherit an already configured API framework,
- dependency management remains incremental,
- later chapters can focus on business logic instead of framework installation.

This approach aligns with the project's philosophy of establishing shared infrastructure before implementing domain functionality.