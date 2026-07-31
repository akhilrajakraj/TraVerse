# Chapter 02 — Django Application Scaffolding

## Chapter Overview

Chapter 02 establishes the foundational application architecture of the TraVerse backend. Rather than immediately implementing business logic or database models, this chapter focuses on creating a clean, scalable, and maintainable Django application structure.

The objective is to prepare the project for future development by creating all application boundaries before introducing domain logic. This approach mirrors the workflow commonly adopted in enterprise software projects, where architecture is established before implementation.

By the end of this chapter, every core application exists within the project, Django recognizes each application correctly, and the project successfully passes Django's built-in validation checks.

---

# Objectives

The primary objectives of this chapter are:

- Create the complete Django application architecture.
- Organize applications under the `backend/apps` package.
- Configure every application with the correct `AppConfig`.
- Register every application inside Django's `INSTALLED_APPS`.
- Verify that the project remains healthy using Django's system checks.
- Build reusable automation scripts to eliminate repetitive setup tasks.

---

# Scope

This chapter includes:

- Django application creation
- Application package organization
- AppConfig configuration
- Django settings registration
- Project validation
- Engineering automation

This chapter intentionally excludes:

- Database models
- Serializers
- Views
- URLs
- Services
- Business logic
- API implementation
- Authentication logic

Those topics are introduced in later chapters.

---

# Application Architecture

The following Django applications were created during this chapter.

| Application | Responsibility |
|-------------|----------------|
| core | Shared platform infrastructure |
| accounts | Authentication and user management |
| travelers | Traveler profiles and preferences |
| destinations | Destination catalogue |
| trips | Trip management |
| planner | Intelligent travel planning |
| itinerary | Itinerary generation |
| ai | AI integrations and orchestration |
| chat | Conversational assistant |
| documents | Travel documents |
| notifications | Notification management |
| payments | Payment processing |
| bookings | Booking management |
| analytics | Reporting and analytics |

All applications reside inside:

```text
backend/apps/
```

---

# Engineering Decisions

Several architectural decisions were made during this chapter.

## Single Application Root

All Django applications are stored beneath a single package.

```text
backend/apps/
```

instead of placing applications directly beside `manage.py`.

This provides:

- cleaner project organization
- consistent imports
- easier scalability
- improved maintainability

---

## Explicit AppConfig

Every application uses an explicit AppConfig.

Example:

```python
name = "apps.core"
```

instead of

```python
name = "core"
```

This ensures Django imports applications using their fully qualified package path.

---

## Automation First

Rather than manually creating fourteen Django applications, engineering automation scripts were introduced.

These scripts perform repetitive tasks consistently and reduce the possibility of human error.

---

# Deliverables

At the completion of this chapter the project contains:

- fourteen Django applications
- configured AppConfig classes
- registered INSTALLED_APPS
- reusable engineering scripts
- successful Django validation

---

# Validation Criteria

Chapter 02 is considered complete when:

- All application directories exist.
- Every application contains a valid AppConfig.
- Every AppConfig points to `apps.<application>`.
- Every application is registered in `INSTALLED_APPS`.
- Django reports no configuration errors.

Validation command:

```bash
python manage.py check
```

Expected output:

```text
System check identified no issues (0 silenced).
```

---

# Outcome

Chapter 02 successfully establishes the application architecture that the remainder of the TraVerse platform will build upon.

Subsequent chapters can now focus entirely on domain modelling, services, APIs, and business logic without requiring further structural changes to the Django project.