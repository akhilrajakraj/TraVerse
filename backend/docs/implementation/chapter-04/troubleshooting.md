# Chapter 04 — Troubleshooting

## Overview

This document records every significant issue encountered during the implementation of the Accounts application and the solutions applied.

The purpose of this document is to reduce debugging time for future contributors by documenting both the symptoms and their root causes.

---

# Issue 01 — Django REST Framework Not Available

## Symptom

Importing DRF inside the Django container failed.

Example:

```python
from rest_framework.permissions import BasePermission
```

Result:

```text
ModuleNotFoundError: No module named 'rest_framework'
```

---

## Cause

The package had not yet been installed inside the Docker image.

---

## Resolution

- Added Django REST Framework to project requirements.
- Rebuilt the Docker image.
- Restarted the Docker containers.
- Verified the installation inside the Django container.

---

# Issue 02 — Visual Studio Code Could Not Resolve DRF Imports

## Symptom

Although Django REST Framework worked correctly inside Docker, Visual Studio Code displayed unresolved import warnings.

---

## Cause

Docker and the local Python virtual environment are independent execution environments.

The package existed inside Docker but was not installed locally.

---

## Resolution

Installed the same package inside the local virtual environment exclusively for editor support.

Docker remained the authoritative runtime environment.

---

# Issue 03 — AUTH_USER_MODEL Conflict

## Symptom

Running:

```bash
python manage.py check
```

produced reverse accessor conflicts between:

- auth.User
- accounts.User

---

## Cause

The custom User model had been implemented before configuring:

```python
AUTH_USER_MODEL
```

Django therefore attempted to load both authentication models simultaneously.

---

## Resolution

Configured:

```python
AUTH_USER_MODEL = "accounts.User"
```

before generating any migrations.

The project then recognized only the custom authentication model.

---

# Issue 04 — Existing Authentication Migrations

## Symptom

The development database already contained Django authentication migrations.

---

## Cause

The inherited infrastructure database had previously executed:

```bash
python manage.py migrate
```

before the custom User model existed.

---

## Resolution

The PostgreSQL Docker volume was removed and recreated.

Authentication implementation restarted using a completely clean database.

---

# Issue 05 — BigAutoField Generated Instead of UUID

## Symptom

The first generated migration created:

```python
id = models.BigAutoField(...)
```

instead of a UUID field.

---

## Cause

The User model inherited only TimeStampedModel.

The shared UUID base model was not included.

---

## Resolution

The User model was updated to inherit:

```python
UUIDPrimaryKeyModel
```

The migration was deleted, regenerated, reviewed, and only then applied.

No migrations had yet been executed, making the correction completely safe.

---

# Issue 06 — Serializer Exceptions

## Symptom

Serializer tests failed with uncaught exceptions.

Example:

```text
InvalidCredentials
```

propagated outside the serializer.

---

## Cause

Custom ApplicationError subclasses were raised directly from Django REST Framework serializers.

DRF expects serializer validation failures to raise:

```python
serializers.ValidationError
```

---

## Resolution

Serializer validation now raises:

```python
serializers.ValidationError
```

Domain exceptions remain reserved for the future service layer.

This separation aligns with Django REST Framework architecture while preserving reusable business exceptions.

---

# Issue 07 — Reviewing Generated Migrations

## Observation

The first generated migration represents the permanent authentication foundation.

Applying an incorrect migration would require unnecessary corrective migrations.

---

## Resolution

A permanent engineering workflow was adopted.

Before any migration is applied:

1. Generate migration.
2. Review migration.
3. Verify generated schema.
4. Apply migration.

No migration should be executed without review.

---

# Issue 08 — Docker Development Workflow

## Observation

Running Django commands from different environments caused inconsistent behaviour.

---

## Resolution

Docker became the single authoritative runtime environment.

All project commands are executed inside:

```bash
docker compose exec django bash
```

The local virtual environment exists only to support:

- IntelliSense
- Static analysis
- Editor tooling

---

# Best Practices Established

During Chapter 04 several permanent engineering practices were adopted.

- Review existing files before modifying them.
- Generate complete files instead of partial snippets.
- Review generated migrations before applying them.
- Validate every phase independently.
- Test incrementally instead of testing everything at the end.
- Perform irreversible operations only after verification.
- Keep Docker as the primary execution environment.

These practices become the standard development workflow for the remainder of the TraVerse project.