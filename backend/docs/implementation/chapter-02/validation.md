# Chapter 02 — Validation

## Purpose

This document defines the validation process for Chapter 02.

Unlike the implementation documentation, this document focuses solely on verifying that the project has been configured correctly. It serves as the acceptance criteria for the chapter and provides a repeatable checklist that can be used by future contributors after recreating the application architecture.

---

# Validation Objectives

The purpose of validation is to confirm that:

- All Django applications have been created successfully.
- Every application resides under the `backend/apps` package.
- Every application contains a correctly configured `AppConfig`.
- Every application has been registered inside Django.
- The project starts without configuration errors.
- Django successfully validates the project configuration.

---

# Expected Project Structure

The following application structure should exist.

```text
backend/
└── apps/
    ├── accounts/
    ├── ai/
    ├── analytics/
    ├── bookings/
    ├── chat/
    ├── core/
    ├── destinations/
    ├── documents/
    ├── itinerary/
    ├── notifications/
    ├── payments/
    ├── planner/
    ├── travelers/
    └── trips/
```

---

# Application Verification

Verify that every application contains the expected files.

Example:

```text
apps/
└── core/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── migrations/
    ├── models.py
    ├── tests.py
    └── views.py
```

Every application should follow the same structure.

---

# AppConfig Verification

Every application should define a valid `AppConfig`.

Example:

```python
from django.apps import AppConfig


class CoreConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.core"

    verbose_name = "Core"
```

Validation checklist:

- `default_auto_field` exists.
- `name` uses the fully qualified package path.
- `verbose_name` is defined.

---

# INSTALLED_APPS Verification

Open:

```text
config/settings.py
```

Verify that all applications are registered.

Expected entries:

```python
"apps.core",
"apps.accounts",
"apps.travelers",
"apps.destinations",
"apps.trips",
"apps.planner",
"apps.itinerary",
"apps.ai",
"apps.chat",
"apps.documents",
"apps.notifications",
"apps.payments",
"apps.bookings",
"apps.analytics",
```

No duplicates should exist.

---

# Django System Validation

Run:

```bash
python manage.py check
```

Expected output:

```text
System check identified no issues (0 silenced).
```

Any errors must be resolved before proceeding to the next chapter.

---

# Automation Verification

Verify that the engineering scripts exist.

```text
scripts/
├── scaffold_apps.py
├── fix_app_configs.py
├── register_apps.py
└── scaffold_docs.py
```

Each script should execute without errors.

---

# Documentation Verification

Confirm that the following documentation has been completed.

```text
docs/
└── implementation/
    └── chapter-02/
        ├── overview.md
        ├── implementation.md
        ├── troubleshooting.md
        ├── lessons-learned.md
        └── validation.md
```

---

# Acceptance Checklist

Mark each item before closing Chapter 02.

| Requirement | Status |
|------------|--------|
| All application directories created | ☐ |
| Fourteen Django applications exist | ☐ |
| Every AppConfig configured | ☐ |
| Every AppConfig uses `apps.<application>` | ☐ |
| `verbose_name` configured | ☐ |
| Applications registered in `INSTALLED_APPS` | ☐ |
| No duplicate registrations | ☐ |
| Django system check passes | ☐ |
| Engineering scripts verified | ☐ |
| Documentation completed | ☐ |

---

# Definition of Done

Chapter 02 is considered complete only when all of the following conditions are satisfied:

- The Django application architecture has been fully scaffolded.
- Every application is correctly configured.
- Django validates the project without errors.
- Automation scripts are functional.
- Documentation has been completed.
- The project is ready to begin domain modelling.

---

# Final Validation Result

**Validation Command**

```bash
python manage.py check
```

**Observed Result**

```text
System check identified no issues (0 silenced).
```

**Chapter Status**

> ✅ **PASSED**

The TraVerse project has successfully completed Chapter 02 and is ready to proceed to Chapter 03.