# Chapter 04 — Implementation

## Overview

Chapter 04 transformed the reusable infrastructure established during Chapter 03 into the first domain application of the TraVerse platform.

This chapter implemented the project's authentication system, introduced the custom User model, configured JSON Web Token (JWT) authentication, and established the identity architecture that every subsequent application will depend upon.

Implementation was performed incrementally, with every phase independently validated before progressing to the next.

---

# Implementation Phases

## Phase 00 — Pre-flight Verification

Before implementing the authentication system, the project state was verified.

Validation included:

- Docker environment
- PostgreSQL container
- Redis container
- Installed applications
- Migration status
- Active authentication model
- Django REST Framework installation

During verification it was discovered that the PostgreSQL database already contained Django's default authentication migrations.

Since a custom User model must be introduced before the first migration is applied, the development database was reset.

The PostgreSQL volume was recreated before continuing implementation.

---

## Phase 01 — Dependency Installation

The following package was introduced:

```text
djangorestframework-simplejwt==5.5.1
```

Implementation included:

- Updating project requirements
- Rebuilding the Docker image
- Restarting containers
- Verifying installation inside the Django container
- Installing the dependency inside the local development virtual environment for Visual Studio Code IntelliSense

Docker remained the authoritative runtime environment throughout development.

---

## Phase 02 — Custom User Manager

A custom UserManager was implemented.

Responsibilities include:

- creating regular users
- creating superusers
- normalizing email addresses
- password hashing
- enforcing required authentication fields

The manager became the single entry point for creating User objects throughout the project.

---

## Phase 03 — Custom User Model

The project replaced Django's default authentication model with a custom User model.

Implementation included:

- removing username authentication
- introducing unique email authentication
- inheriting shared timestamp infrastructure
- integrating the custom UserManager
- configuring email as USERNAME_FIELD

---

## Phase 04 — Authentication Configuration

Project-wide authentication settings were configured.

Configuration included:

- AUTH_USER_MODEL
- REST_FRAMEWORK
- SIMPLE_JWT
- JWT authentication classes

Once configured, Django correctly recognized the custom User model as the project's authentication model.

---

## Phase 05 — Global Exception Handler

A centralized Django REST Framework exception handler was implemented.

The handler provides a consistent API response format for future REST endpoints across the platform.

Instead of each application implementing independent exception formatting, response handling now remains centralized.

---

## Phase 06 — Account Exceptions

Account-specific exceptions were introduced.

These exceptions extend the reusable application exception hierarchy implemented during Chapter 03.

This separates authentication-specific failures from generic application errors.

---

## Phase 07 — Authentication Serializers

Three serializers were implemented.

### RegisterSerializer

Responsible for:

- validating email uniqueness
- hashing passwords
- creating users

### LoginSerializer

Responsible for:

- validating credentials
- authenticating users
- validating account status

### UserSerializer

Responsible for:

- authenticated user representation
- profile serialization
- read-only user responses

---

## Phase 08 — Authentication Views

REST API endpoints were implemented for:

- registration
- login
- logout
- authenticated user retrieval

JWT access and refresh tokens are generated during successful authentication.

---

## Phase 09 — URL Configuration

Authentication endpoints were connected to the project router.

The Accounts application now exposes:

```text
/api/accounts/register/
/api/accounts/login/
/api/accounts/logout/
/api/accounts/me/
```

Future frontend and mobile applications will consume these endpoints.

---

## Phase 10 — Django Admin

The custom User model was registered with Django Admin.

Configuration included:

- custom list display
- search fields
- filters
- readonly fields
- custom fieldsets
- UUID-compatible administration

This provides complete administrative management of user accounts.

---

## Phase 11 — Initial Migration

Before generating the first migration, the implementation underwent a final architectural review.

Verification confirmed:

- custom User model active
- AUTH_USER_MODEL configured
- no applied migrations
- successful imports
- clean project configuration

The initial migration was then generated.

During review, the generated migration originally used BigAutoField as the primary key.

Before applying migrations, the architecture was refined to adopt UUID primary keys using the reusable UUID infrastructure introduced during Chapter 03.

The original migration was discarded, regenerated, reviewed, and then applied successfully.

This ensured a consistent identifier strategy across the entire TraVerse platform.

---

## Phase 12 — Automated Testing

Authentication infrastructure was validated using automated tests.

Test coverage included:

- User model
- User manager
- Serializers
- API views
- Django Admin configuration

A complete Accounts application test suite was executed after all individual test groups passed.

---

# Development Workflow

Implementation followed a disciplined incremental workflow.

Each phase consisted of:

1. Implementation
2. Django validation
3. Targeted testing
4. Issue resolution
5. Architectural review
6. Progression to the next phase

This approach minimized debugging complexity and prevented architectural issues from propagating through later implementation stages.

---

# Docker Workflow

Development was performed inside the Django Docker container.

Typical workflow:

```bash
docker compose exec django bash
```

All Django commands, migrations, testing, and validation were executed from inside the container.

The local Python virtual environment was maintained primarily for Visual Studio Code features such as IntelliSense and static analysis.

Docker remained the authoritative execution environment throughout implementation.

---

# Final Outcome

By the conclusion of Chapter 04, the TraVerse platform possessed a production-ready authentication foundation built upon a custom UUID-based User model.

The authentication architecture, database schema, REST API, administrative interface, and automated test suite were fully implemented, validated, and prepared for future domain applications.