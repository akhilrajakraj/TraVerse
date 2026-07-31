# Chapter 2 — Django Project Skeleton & App Registration

**Volume 1: Foundations | Chapter 2 of 29**

> This chapter creates every Django app as an *empty shell* — no models, no views, no business logic — in the exact dependency order fixed by Architecture Handbook §4.3. The goal is a project that boots cleanly with `python manage.py check` reporting zero errors, with every app wired in but nothing inside them yet. Chapter 3 onward fills these shells in, one at a time.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Create a full set of empty Django apps under `apps/` without breaking Django's app-loading system.
- Correctly register apps in `INSTALLED_APPS` in dependency order.
- Understand why `apps.py`'s `name` attribute must match the real import path when apps live in a subpackage (`apps/`) instead of the project root.
- Prove the skeleton is sound using `python manage.py check`, before any model exists to hide a misconfiguration.

---

## 2. Theory

### 2.1 What Is a Django "App," Really? (ELI10)

A Django "app" is just a folder with a specific, predictable shape that Django knows how to recognize — a bit like a labeled box in a warehouse. Django doesn't care what's *inside* the box yet; it only cares that the box has the right label (`apps.py`) and the right shape (`__init__.py`, `migrations/`, etc.) so it can find it later when you *do* put things inside.

### 2.2 Why Empty Apps Before Any Models

If you create a model and register the app in the same step, and something breaks, you don't know if the break came from (a) Django not finding the app at all, or (b) a bad field in the model. Separating "does Django even see this app" from "is this app's content correct" is the same debugging discipline from Chapter 1, just one layer up.

### 2.3 Why `apps/` As a Subpackage Instead Of Apps At The Project Root

Default Django tutorials put apps like `accounts/` directly next to `manage.py`. We instead nest them under `apps/accounts/`. This is a deliberate enterprise convention:
- It visually and structurally separates "project plumbing" (`config/`) from "business logic" (`apps/`) — matching Architecture Handbook §3.2.
- It scales cleanly to dozens of apps without cluttering the project root.
- It requires one extra piece of care: `apps.py`'s `name` must be the dotted path `apps.accounts`, not just `accounts`, or Django's app registry will not resolve model references correctly (see Section 12).

---

## 3. Architecture Decision

**Decision:** All 14 apps from Architecture Handbook §4.2 are created as empty shells in this single chapter, registered in `INSTALLED_APPS` in the dependency order from §4.3, but **no models are defined yet** — not even the custom `User` model.

**Why not create the `User` model now, since it's "first"?** Creating the User model is significant enough (Section 5.9 of the Architecture Handbook — a decision that can't be undone later without pain) that it deserves its own chapter (Chapter 4) with full attention, rather than being rushed in alongside 13 other empty folders. This chapter is purely structural.

**Alternative considered:** Create apps one at a time, only right before each is filled in. **Rejected because:** `INSTALLED_APPS` ordering matters for Django's app registry resolution, and getting the *entire* order right once, verified with `check`, is less error-prone than repeatedly editing a growing settings list across 14 separate chapters.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Create `apps/` folder + `__init__.py` | Makes it an importable Python package — nothing works without this |
| Create each app via `startapp`, then move it | Django's own tool generates the correct boilerplate; manually hand-writing it risks typos in files Django is picky about (`apps.py`) |
| Fix each `apps.py` `name` attribute | Required because we moved the app into a subpackage after generation |
| Register in `INSTALLED_APPS` in dependency order | Prevents subtle app-loading order bugs later (e.g., admin autodiscovery, signal registration order) |
| Run `check` after every few apps, not just at the end | If something breaks, you know it was introduced in the last 2-3 apps, not somewhere in 14 |

---

## 5. File Structure (Target State After This Chapter)

```
apps/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── apps.py
│   ├── migrations/
│   │   └── __init__.py
├── accounts/          (same shape as core)
├── profiles/
├── destinations/
├── trips/
├── itinerary/
├── budget/
├── recommendations/
├── ai_agents/
├── chat/
├── documents/
├── notifications/
├── bookings/
└── analytics/
```

Each app folder, at this stage, contains **only**: `__init__.py`, `apps.py`, and an empty `migrations/__init__.py`. Django auto-generates `models.py`, `admin.py`, `views.py`, `tests.py` via `startapp` — we deliberately **empty these out** to true placeholders (a docstring only) rather than leaving Django's default boilerplate content, so Chapter-by-chapter diffs are clean later.

---

## 6. Folder Location

All commands run from `project-root/`. The `apps/` folder sits directly beside `config/` and `manage.py`, per Architecture Handbook §3.1.

---

## 7. Terminal Commands

### 7.1 Create the `apps/` Package

```bash
mkdir -p apps
touch apps/__init__.py
```

### 7.2 Generate Each App Using Django's Own Tooling

Django's `startapp` command must be told to output *into* `apps/<name>`, and this must be run **inside the container** (so it uses the exact Django version/Python version the platform runs), not on your host machine:

```bash
docker compose exec web python manage.py startapp core apps/core
docker compose exec web python manage.py startapp accounts apps/accounts
docker compose exec web python manage.py startapp profiles apps/profiles
docker compose exec web python manage.py startapp destinations apps/destinations
docker compose exec web python manage.py startapp trips apps/trips
docker compose exec web python manage.py startapp itinerary apps/itinerary
docker compose exec web python manage.py startapp budget apps/budget
docker compose exec web python manage.py startapp recommendations apps/recommendations
docker compose exec web python manage.py startapp ai_agents apps/ai_agents
docker compose exec web python manage.py startapp chat apps/chat
docker compose exec web python manage.py startapp documents apps/documents
docker compose exec web python manage.py startapp notifications apps/notifications
docker compose exec web python manage.py startapp bookings apps/bookings
docker compose exec web python manage.py startapp analytics apps/analytics
```

**Why this exact order:** it is the dependency order from Architecture Handbook §4.3 — `core` first (nothing depends on it, it depends on nothing), `analytics` last (depends on everything, as a read-only consumer).

**Why 14 separate commands instead of a loop:** at this stage, running each one individually means if command #6 fails, you see exactly which app failed, with its own error output, instead of a swallowed loop error.

---

## 8. Docker Commands

### 8.1 Confirm the Container Sees the New Files (Bind Mount Sanity Check)

```bash
docker compose exec web ls apps/
```

Expected: all 14 folder names listed.

### 8.2 Restart Django After Settings Changes

```bash
docker compose restart web
```

**Why restart, not just save the file:** Django's `INSTALLED_APPS` and app registry are only read once at process startup. Editing `settings/base.py` while Gunicorn is already running does not take effect until the worker process restarts — a very common source of "I fixed it but it's still broken" confusion.

---

## 9. Expected Output

### 9.1 `apps.py` As Generated (Example: `accounts`)

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
```

This is **wrong for our structure** — see Section 10 for the required fix.

### 9.2 `python manage.py check` Success Output

```
System check identified no issues (0 silenced).
```

Anything else at this stage means an app is misconfigured — do not proceed until you see exactly this line.

---

## 10. Code

### 10.1 Fixed `apps.py` Pattern (Applied to All 14 Apps)

Every generated `apps.py` needs its `name` corrected to the full dotted path, and gets a human-readable `verbose_name` for the admin site later:

```python
# apps/accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"
```

Repeat this pattern for all 14 apps — only `name`'s suffix and the class name / `verbose_name` change:

```python
# apps/core/apps.py
class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

# apps/profiles/apps.py
class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    verbose_name = "Traveler Profiles"

# apps/destinations/apps.py
class DestinationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.destinations"
    verbose_name = "Destinations"

# apps/trips/apps.py
class TripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trips"
    verbose_name = "Trips"

# apps/itinerary/apps.py
class ItineraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.itinerary"
    verbose_name = "Itinerary"

# apps/budget/apps.py
class BudgetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.budget"
    verbose_name = "Budget"

# apps/recommendations/apps.py
class RecommendationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recommendations"
    verbose_name = "Recommendations"

# apps/ai_agents/apps.py
class AiAgentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_agents"
    verbose_name = "AI Agents"

# apps/chat/apps.py
class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat"
    verbose_name = "Chat"

# apps/documents/apps.py
class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "Documents"

# apps/notifications/apps.py
class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"

# apps/bookings/apps.py
class BookingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.bookings"
    verbose_name = "Bookings"

# apps/analytics/apps.py
class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "Analytics"
```

### 10.2 Emptying Out Generated Boilerplate Files

For every app, replace Django's default `models.py`, `views.py`, `admin.py`, and `tests.py` content with an intentional placeholder docstring, so it's explicit these are deliberately empty, not forgotten:

```python
# apps/<name>/models.py
"""
Models for the <name> app.
Intentionally empty — implemented in its dedicated chapter.
See docs/Implementation_Bible for build order.
"""
```

(Same pattern for `admin.py`, `views.py`, `tests.py` — only the docstring's app name changes.)

### 10.3 `config/settings/base.py` — App Registration

```python
# config/settings/base.py  (excerpt — only the INSTALLED_APPS section changes)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # DockForge-provided third-party apps stay exactly as they already were —
    # nothing here is removed or reordered.
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.profiles",
    "apps.destinations",
    "apps.trips",
    "apps.itinerary",
    "apps.budget",
    "apps.recommendations",
    "apps.ai_agents",
    "apps.chat",
    "apps.documents",
    "apps.notifications",
    "apps.bookings",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
```

---

## 11. Code Walkthrough

- **Why split `INSTALLED_APPS` into three named lists instead of one flat list:** it documents *intent*. Anyone reading this file instantly knows which apps are Django's own, which are third-party packages DockForge already depends on, and which are ours — without needing a comment above every single line.
- **Why `LOCAL_APPS` keeps the exact §4.3 order:** Django loads apps' `models.py` and registers signals in `INSTALLED_APPS` order. While Django is generally tolerant of ordering for simple cases, keeping our declared order identical to our *dependency* order means that if a subtle ordering bug ever appears (e.g., in signal registration in Chapter 5), the fix is "look at the order," not "guess."
- **Why `name = "apps.accounts"` and not `"accounts"`:** Django's app registry (`django.apps.apps`) uses this string to import the app's models module. Since the real Python import path is `apps.accounts.models`, the `name` must match that exactly, or Django raises `ImproperlyConfigured` at boot (see Section 12).
- **Why empty `models.py`/`views.py`/etc. still exist with docstrings, not deleted:** Django's app-loading assumes standard files exist for tooling and later `startapp`-adjacent conventions (and every future chapter's diff will show a clean "docstring → real content" change, which is a much more reviewable git history than "new file created").

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `django.core.exceptions.ImproperlyConfigured: Cannot import 'accounts'. Check that 'apps.accounts.apps.AccountsConfig.name' is correct.` | `apps.py`'s `name` still says `"accounts"` instead of `"apps.accounts"` after moving the folder | Fix `name` to full dotted path (Section 10.1) |
| `ModuleNotFoundError: No module named 'apps'` | Missing `apps/__init__.py` | `touch apps/__init__.py` |
| App silently "not found" (no error, but models never appear in admin later) | App listed in wrong list or misspelled string in `INSTALLED_APPS` | Diff `INSTALLED_APPS` against Section 10.3 exactly |
| `RuntimeError: Model class apps.trips.models.Trip doesn't declare an explicit app_label...` (in later chapters) | Symptom of the same root cause as the first row — `name` mismatch | Same fix — always check `apps.py` first for this error family |

---

## 13. Debugging

```bash
# 1. Confirm Django can even discover all apps
docker compose exec web python manage.py check

# 2. If check fails, isolate which app by commenting out LOCAL_APPS entries
#    one at a time (temporarily) and re-running check — this bisection
#    approach finds the broken app in log2(14) ≈ 4 attempts, not 14.

# 3. Confirm the app registry sees exactly what you expect
docker compose exec web python manage.py shell -c \
  "from django.apps import apps; print([a.name for a in apps.get_app_configs()])"

# 4. If Gunicorn is running stale code, force a full restart (not reload)
docker compose restart web
```

**Rollback strategy:** since no migrations exist yet for any of these apps, there is no database state to worry about — worst case, delete the offending app's folder and re-run `startapp` for it alone.

---

## 14. Testing

No business-logic tests exist yet (there's no logic). The verification for this chapter is entirely structural:

```bash
docker compose exec web python manage.py check
# Expected: "System check identified no issues (0 silenced)."

docker compose exec web python manage.py shell -c \
  "from django.apps import apps; assert len(apps.get_app_configs()) >= 14 + 6 + 3; print('OK')"
# (6 Django built-ins, 3 third-party, 14 local — adjust the third-party
# count to match whatever DockForge's base.py already includes)
```

---

## 15. Git Commit

```bash
git add apps/ config/settings/base.py
git commit -m "feat(scaffold): create empty app shells and register in INSTALLED_APPS

Creates all 14 application-layer apps (core, accounts, profiles,
destinations, trips, itinerary, budget, recommendations, ai_agents,
chat, documents, notifications, bookings, analytics) as empty shells
in dependency order per Architecture Handbook §4.3.

No models, views, or business logic implemented yet — each app is
filled in during its own dedicated chapter. 'manage.py check' passes
with zero issues.

Chapter 2 of Implementation Bible."
```

**Why one commit for all 14 apps, unlike later chapters which get one commit each:** these are structurally identical empty shells with no independent behavior to verify separately — splitting this into 14 commits would add noise without adding reviewability. From Chapter 3 onward, each app gets its own commit(s), because each one introduces real, independently-reviewable logic.

---

## 16. Checklist

- [ ] `apps/__init__.py` exists
- [ ] All 14 app folders created via `startapp`, moved under `apps/`
- [ ] Every `apps.py`'s `name` corrected to `apps.<name>` dotted path
- [ ] Every generated `models.py`/`admin.py`/`views.py`/`tests.py` replaced with an intentional placeholder docstring
- [ ] `INSTALLED_APPS` in `config/settings/base.py` updated in exact §4.3 order
- [ ] `docker compose restart web` performed after settings changes
- [ ] `python manage.py check` returns zero issues
- [ ] Single scaffold commit made with a clear message

---

## 17. Next Chapter Preview

**Chapter 3 — `core` App: Shared Foundations** fills in the very first app: `TimeStampedModel` and other abstract base models, shared mixins, a base exception class, and shared DRF permission classes that every later app will import. This is the one app every other app in the project depends on, so it gets built — and tested — before anything else touches real data. Say **"Continue to Chapter 3"** when ready.
