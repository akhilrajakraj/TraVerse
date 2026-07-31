# Chapter 03 — Troubleshooting

## Overview

This document records the issues encountered during the implementation of the `core` application and the solutions applied to resolve them.

Recording these issues provides future contributors with context and helps avoid repeating the same mistakes.

---

# Issue 1 — Django REST Framework Not Installed

## Symptoms

While implementing `permissions.py`, the following import could not be resolved:

```python
from rest_framework.permissions import BasePermission
```

Visual Studio Code displayed an unresolved import warning.

Running the following command inside the Django shell produced:

```text
ModuleNotFoundError: No module named 'rest_framework'
```

---

## Root Cause

The project had not yet included Django REST Framework as a dependency.

Although the permission classes had been implemented correctly, the required package was missing from the Python environment.

---

## Resolution

Added Django REST Framework to the base requirements.

```text
backend/requirements/base.txt
```

```text
djangorestframework==3.16.1
```

Rebuilt the Docker image:

```bash
docker compose \
-f infrastructure/compose/docker-compose.yml \
-f infrastructure/compose/docker-compose.dev.yml \
build django
```

Restarted the containers:

```bash
docker compose \
-f infrastructure/compose/docker-compose.yml \
-f infrastructure/compose/docker-compose.dev.yml \
up -d
```

Registered the application:

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
]
```

Verification:

```bash
python manage.py check
```

Result:

```
System check identified no issues.
```

---

# Issue 2 — Local Virtual Environment Used the Wrong pip

## Symptoms

The Docker environment successfully imported Django REST Framework.

However, Visual Studio Code continued reporting:

```python
from rest_framework.permissions import BasePermission
```

as an unresolved import.

Running:

```bash
python -c "from rest_framework.permissions import BasePermission"
```

failed locally.

---

## Investigation

Inspection revealed that:

- `python` was executing from the TraVerse virtual environment.
- `pip` was installing packages into a different project's virtual environment.

The executables pointed to different locations.

---

## Root Cause

The system PATH referenced a different virtual environment.

As a result:

- Python interpreter → TraVerse
- pip executable → another project

Packages were installed into the wrong environment.

---

## Resolution

Verified the active interpreter:

```bash
python -m pip -V
```

Installed packages using:

```bash
python -m pip install djangorestframework==3.16.1
```

instead of:

```bash
pip install ...
```

This ensured that pip and Python referred to the same virtual environment.

---

# Issue 3 — Abstract Models Produced No Migrations

## Observation

Executing:

```bash
python manage.py makemigrations core --check --dry-run
```

reported:

```
No changes detected.
```

Initially, this appeared unexpected.

---

## Explanation

All shared models were intentionally declared abstract.

```python
class Meta:
    abstract = True
```

Abstract models are inherited by concrete models and therefore do not generate database tables or migrations.

This behavior confirmed the implementation was correct.

---

# Issue 4 — Testing Strategy

## Observation

Instead of Django's default:

```text
tests.py
```

the project adopted:

```text
tests/
├── __init__.py
├── test_models.py
├── test_exceptions.py
└── test_permissions.py
```

---

## Reason

As the project grows, a package-based testing structure scales significantly better than a single test file.

This structure will be used consistently across all future applications.

---

# Lessons from This Chapter

The implementation reinforced several engineering practices:

- Validate each implementation phase independently.
- Keep reusable infrastructure isolated from business logic.
- Prefer abstract models for shared functionality.
- Use `python -m pip` to avoid virtual environment mismatches.
- Rebuild Docker images after modifying dependency files.
- Maintain a scalable testing structure from the beginning of the project.

---

# Outcome

All identified issues were successfully resolved.

The final implementation passed:

- Django system checks
- Model tests
- Exception tests
- Permission tests
- Complete `core` application test suite

No outstanding issues remained at the conclusion of Chapter 03.