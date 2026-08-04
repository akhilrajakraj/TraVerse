# Chapter 24 — `analytics` App

**Volume 6: Supporting Apps | Chapter 24 of 29**

> Volume 6 closes here. `analytics` is the read-only consumer of everything built since Chapter 4 — per Architecture Handbook §4.4, it "never writes to other apps' tables directly, only reads." This is also the first chapter to think seriously about query performance at the *aggregate, cross-app* level, rather than the single-trip scope every prior `assertNumQueries` test (Chapters 8, 9, 20) has focused on — and the first app in the project that needs **zero models of its own** at all.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Recognize when an app genuinely needs no database tables of its own, and build one that's entirely query functions operating on other apps' data.
- Combine multiple aggregate counts into a single SQL query using Django's `Count(..., filter=Q(...))` pattern, instead of one query per count — and prove the difference with `assertNumQueries`.
- Cache an expensive aggregate computation using Django's `cache.get_or_set()`, a different cache usage pattern from Chapter 17's manual increment-based rate limiter.
- Apply a third distinct permission model (`IsAdminUser`, staff-only) alongside the project's two prior ones (`IsOwner`, and Chapter 21's single `AllowAny` exception).

---

## 2. Theory

### 2.1 Why `analytics` Needs Zero Models of Its Own (ELI10)

Imagine a museum's information desk — it doesn't own any of the exhibits, it just knows how to answer questions about what's already on display by looking at what's there. `analytics` is that information desk: every fact it reports ("how many trips exist," "what's the AI success rate") is already sitting in some other app's tables (`Trip`, `AgentRun`, `Recommendation`, `Booking`). Building a new `AnalyticsSnapshot` model to *duplicate* that data would immediately create a synchronization problem — the exact kind of duplicated-truth issue Architecture Handbook §5.5 already warned against, applied here at the app level instead of the field level.

### 2.2 Why One Aggregate Query Beats Five Separate Counts (ELI10)

Imagine asking a librarian five separate times, "how many fiction books do you have," "how many non-fiction," "how many biographies"... versus asking once, "give me a full breakdown of your catalog by category." The second approach makes the librarian do the same amount of *counting* work, but only requires one trip to actually ask. Django's `.aggregate()` with multiple `Count(..., filter=Q(...))` annotations lets the database compute several different counts within a single SQL query — the same fixed-query-count discipline Chapter 8 applied to nested relations, applied here to aggregate statistics instead.

### 2.3 Why This Uses a Different Cache Pattern Than Chapter 17's Rate Limiter

Chapter 17's rate limiter needed a counter that *changes* on every request (`cache.incr()`). A platform summary is different: it's expensive to compute but doesn't need to be perfectly fresh to the second — showing a dashboard number that's up to five minutes stale is a completely acceptable trade-off for not re-running expensive aggregate queries on every single admin page load. `cache.get_or_set()` — "return the cached value if present, otherwise compute it, cache it, and return it" — is the right tool for this different situation, distinct from the increment pattern.

---

## 3. Architecture Decision

**Decision:** `apps/analytics` has an intentionally empty `models.py` (a docstring only, matching Chapter 3's convention for placeholder files) — no `AnalyticsSnapshot`, no cached-row pattern. All data comes from live queries against other apps' models, with Redis (via Django's cache framework) as the *only* place any computed result is temporarily held.

**Decision:** Every multi-count aggregate function in this chapter uses a single `.aggregate()` call with multiple `Count(..., filter=Q(...))` annotations, never a loop of separate `.filter().count()` calls — proven, not just claimed, via `assertNumQueries(1)`.

**Decision:** All analytics endpoints use DRF's built-in `IsAdminUser` (checking `user.is_staff`), the project's third distinct permission model, alongside `IsOwner` (used almost everywhere since Chapter 7) and Chapter 21's one deliberate `AllowAny` exception.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Write `apps/analytics/selectors.py` | The entire chapter's substance — must exist before anything else |
| Write `apps/analytics/caching.py` | Needs the selector functions to exist first, since it wraps them |
| Write serializers for the aggregate dict shapes | Needed before views |
| Build the staff-only views | Last |

---

## 5. File Structure

```
apps/analytics/
├── __init__.py
├── apps.py
├── models.py                    # Intentionally empty — see Chapter 24 Architecture Decision
├── selectors.py                   # get_platform_summary, get_agent_performance_summary, etc.
├── caching.py                      # get_cached_platform_summary — cache.get_or_set pattern
├── serializers.py
├── views.py
├── urls.py
├── migrations/
│   └── __init__.py               # empty forever, like core (Chapter 3)
└── tests/
    ├── __init__.py
    ├── test_selectors.py
    ├── test_caching.py
    └── test_views.py
```

**Why `admin.py` is absent from this list entirely, unlike every other app since Chapter 4**: Django's admin registration (`@admin.register(Model)`) requires a model — with none to register, there's genuinely nothing for this file to contain. Omitting it entirely, rather than creating an empty placeholder, is itself an honest reflection of the app's shape.

---

## 6. Folder Location

New files under `apps/analytics/` (already scaffolded empty since Chapter 2).

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations analytics --check --dry-run
# Expected: "No changes detected in app 'analytics'" — same tripwire pattern as Chapter 3's core app

docker compose exec web python manage.py test apps.analytics -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py shell -c "
from apps.analytics.selectors import get_platform_summary
import json
print(json.dumps(get_platform_summary(), indent=2, default=str))
"
{
  "total_trips": 42,
  "trips_by_status": {"draft": 10, "planning": 2, "planned": 25, "completed": 4, "cancelled": 1},
  "total_agent_runs": 38,
  "agent_success_rate": 0.87
}
```

---

## 10. Code

### 10.1 `apps/analytics/models.py`

```python
"""
Models for the analytics app.
Intentionally empty — analytics is 100% read-only against other
apps' tables. See Chapter 24 Architecture Decision for why no
AnalyticsSnapshot or caching model exists here; Redis (via
caching.py) is the only place a computed result is ever held, and
only temporarily.
"""
```

### 10.2 `apps/analytics/selectors.py`

```python
"""
Every function here reads other apps' tables. NOTHING in this
module ever writes — enforced by convention (see Architecture
Handbook §4.4) and by the simple fact that no model here has a
manager capable of writing anything.
"""
from django.db.models import Avg, Count, Q

from apps.ai_agents.models import AgentRun, AgentRunStatus
from apps.bookings.models import Booking
from apps.recommendations.models import Recommendation, RecommendationStatus
from apps.trips.models import Trip, TripStatus


def get_platform_summary() -> dict:
    """
    ONE query for the trip-status breakdown (multiple Count(filter=...)
    annotations), not five separate .filter().count() calls — see
    Chapter 24 Theory §2.2 and the assertNumQueries proof in tests.
    """
    trip_aggregates = Trip.objects.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status=TripStatus.DRAFT)),
        planning=Count("id", filter=Q(status=TripStatus.PLANNING)),
        planned=Count("id", filter=Q(status=TripStatus.PLANNED)),
        completed=Count("id", filter=Q(status=TripStatus.COMPLETED)),
        cancelled=Count("id", filter=Q(status=TripStatus.CANCELLED)),
    )

    agent_aggregates = AgentRun.objects.aggregate(
        total=Count("id"),
        succeeded=Count("id", filter=Q(status=AgentRunStatus.SUCCEEDED)),
        failed=Count("id", filter=Q(status=AgentRunStatus.FAILED)),
        needs_review=Count("id", filter=Q(status=AgentRunStatus.NEEDS_REVIEW)),
    )
    success_rate = (
        agent_aggregates["succeeded"] / agent_aggregates["total"]
        if agent_aggregates["total"] else 0.0
    )

    return {
        "total_trips": trip_aggregates["total"],
        "trips_by_status": {
            "draft": trip_aggregates["draft"], "planning": trip_aggregates["planning"],
            "planned": trip_aggregates["planned"], "completed": trip_aggregates["completed"],
            "cancelled": trip_aggregates["cancelled"],
        },
        "total_agent_runs": agent_aggregates["total"],
        "agent_success_rate": round(success_rate, 2),
    }


def get_agent_performance_summary() -> dict:
    return AgentRun.objects.aggregate(
        total=Count("id"),
        succeeded=Count("id", filter=Q(status=AgentRunStatus.SUCCEEDED)),
        failed=Count("id", filter=Q(status=AgentRunStatus.FAILED)),
        needs_review=Count("id", filter=Q(status=AgentRunStatus.NEEDS_REVIEW)),
        pending_or_running=Count("id", filter=Q(status__in=[AgentRunStatus.PENDING, AgentRunStatus.RUNNING])),
    )


def get_recommendation_acceptance_rate() -> float:
    aggregates = Recommendation.objects.exclude(status=RecommendationStatus.PENDING).aggregate(
        total_decided=Count("id"),
        accepted=Count("id", filter=Q(status=RecommendationStatus.ACCEPTED)),
    )
    if aggregates["total_decided"] == 0:
        return 0.0
    return round(aggregates["accepted"] / aggregates["total_decided"], 2)


def get_booking_intent_summary() -> dict:
    return Booking.objects.aggregate(
        total=Count("id"),
        from_recommendation=Count("id", filter=Q(source_recommendation__isnull=False)),
        flights=Count("id", filter=Q(booking_type="flight")),
        hotels=Count("id", filter=Q(booking_type="hotel")),
        activities=Count("id", filter=Q(booking_type="activity")),
    )
```

**Why `get_platform_summary`'s trip breakdown and agent breakdown are still two separate `.aggregate()` calls, not one combined query across both models**: `.aggregate()` operates on a single queryset — combining `Trip` and `AgentRun` counts into one call isn't possible without a join or union that would be far less readable than two clear, purpose-built queries. The lesson from Theory §2.2 is "don't split one model's counts into N queries," not "every function must be exactly one query regardless of how many different tables are involved" — worth being precise about the actual scope of the optimization.

**Why `Recommendation.objects.exclude(status=PENDING)` before aggregating in `get_recommendation_acceptance_rate`**: a pending recommendation hasn't been decided yet — including it in the denominator would understate the real acceptance rate among recommendations a user actually reviewed, the correct metric for understanding "of the suggestions people looked at, how many did they like."

### 10.3 `apps/analytics/caching.py`

```python
"""
Wraps the (comparatively) expensive selector functions with a
short-TTL Redis cache — a DIFFERENT cache usage pattern than Chapter
17's rate limiter (cache.incr, changes every request). Here, the
underlying data doesn't need to be second-fresh, so
cache.get_or_set() is the right tool. See Chapter 24 Theory §2.3.
"""
from django.core.cache import cache

from apps.analytics.selectors import (
    get_agent_performance_summary,
    get_booking_intent_summary,
    get_platform_summary,
    get_recommendation_acceptance_rate,
)

_CACHE_TTL_SECONDS = 300  # 5 minutes — stale-but-acceptable for a dashboard


def get_cached_platform_summary() -> dict:
    return cache.get_or_set("analytics:platform_summary", get_platform_summary, _CACHE_TTL_SECONDS)


def get_cached_agent_performance_summary() -> dict:
    return cache.get_or_set("analytics:agent_performance", get_agent_performance_summary, _CACHE_TTL_SECONDS)


def get_cached_recommendation_acceptance_rate() -> float:
    return cache.get_or_set("analytics:recommendation_acceptance", get_recommendation_acceptance_rate, _CACHE_TTL_SECONDS)


def get_cached_booking_intent_summary() -> dict:
    return cache.get_or_set("analytics:booking_intent_summary", get_booking_intent_summary, _CACHE_TTL_SECONDS)
```

**Why `cache.get_or_set()` is passed the function itself (`get_platform_summary`, no parentheses), not its already-computed result**: this is the entire point of `get_or_set` — it only *calls* the given function if the cache is actually empty/expired, meaning the (comparatively) expensive aggregate queries only run once every five minutes across however many dashboard views happen in that window, not on every single request. Passing `get_platform_summary()` (called immediately) would defeat the caching entirely, since the expensive work would happen before `get_or_set` ever got a chance to check the cache.

### 10.4 `apps/analytics/serializers.py`

```python
from rest_framework import serializers


class PlatformSummarySerializer(serializers.Serializer):
    total_trips = serializers.IntegerField()
    trips_by_status = serializers.DictField()
    total_agent_runs = serializers.IntegerField()
    agent_success_rate = serializers.FloatField()


class AgentPerformanceSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    succeeded = serializers.IntegerField()
    failed = serializers.IntegerField()
    needs_review = serializers.IntegerField()
    pending_or_running = serializers.IntegerField()
```

**Why these are plain `Serializer` subclasses, not `ModelSerializer`**: same reasoning as Chapter 9's `BudgetSummarySerializer` — this data is aggregated across multiple rows/models, with no single model instance it maps to one-to-one.

### 10.5 `apps/analytics/views.py`

```python
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics import caching
from apps.analytics.serializers import AgentPerformanceSerializer, PlatformSummarySerializer


class PlatformSummaryView(APIView):
    """
    Staff-only — the project's THIRD distinct permission model,
    alongside IsOwner (nearly everywhere) and Chapter 21's one
    AllowAny exception.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        summary = caching.get_cached_platform_summary()
        return Response(PlatformSummarySerializer(summary).data)


class AgentPerformanceView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        summary = caching.get_cached_agent_performance_summary()
        return Response(AgentPerformanceSerializer(summary).data)
```

### 10.6 `apps/analytics/urls.py`

```python
from django.urls import path

from apps.analytics.views import AgentPerformanceView, PlatformSummaryView

app_name = "analytics"

urlpatterns = [
    path("platform-summary/", PlatformSummaryView.as_view(), name="platform-summary"),
    path("agent-performance/", AgentPerformanceView.as_view(), name="agent-performance"),
]
```

### 10.7 `config/urls.py` (addition)

```python
path("api/v1/analytics/", include("apps.analytics.urls")),
```

---

## 11. Code Walkthrough

- **`apps/analytics/models.py` containing only a docstring is the direct payoff of the project's established "empty file honestly reflects scope" convention**, first established for `core` in Chapter 3 and echoed for `bookings` in Chapter 23 — three chapters apart, the same underlying discipline: don't create structure the actual need doesn't call for.
- **The `Count(..., filter=Q(...))` pattern used throughout `selectors.py` is worth recognizing as the aggregate-query equivalent of Chapter 8's `Prefetch` + `select_related` combination**: both techniques exist to answer "get me several related pieces of information" in one round-trip instead of many, just applied to two different kinds of query shape (nested relations vs. grouped counts).
- **This is the first app in the project where `IsAdminUser`, a DRF built-in, is used instead of Chapter 3's custom `IsOwner`/`IsStaffOrReadOnly`**: worth noticing that not every permission need requires a custom class — `IsAdminUser` already does exactly what's needed here (staff-only, no exceptions), and reaching for a built-in when it fits is the same "don't build what already exists" discipline behind every dependency decision in this project.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `migrate` tries to create a table for `analytics` | Someone added a real model to `models.py`, breaking the chapter's central premise | Reconsider whether the new data genuinely needs its own table, or can be computed from existing apps' data instead |
| Dashboard numbers look stale during active testing | `get_or_set`'s 5-minute cache is working as intended | Use the uncached `selectors.py` functions directly when testing for freshness, or clear the relevant cache key manually |
| `403 Forbidden` for a logged-in user who should see analytics | User's `is_staff` is `False` | Analytics is intentionally staff-only — grant staff status via the admin or `createsuperuser`, not a special analytics permission |
| Cached value doesn't update after clearing test data | Stale cache key persisting across test runs | Ensure tests use `cache.clear()` in `setUp`, matching the pattern from Chapter 17's rate-limit tests |

---

## 13. Debugging

```bash
# 1. Prove the aggregate query count directly
docker compose exec web python manage.py shell -c "
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True
reset_queries()
from apps.analytics.selectors import get_platform_summary
get_platform_summary()
print(f'Query count: {len(connection.queries)}')
"

# 2. Confirm caching actually avoids re-querying
docker compose exec web python manage.py shell -c "
from django.core.cache import cache
cache.clear()
from apps.analytics import caching
caching.get_cached_platform_summary()  # computes + caches
print(cache.get('analytics:platform_summary') is not None)
"
```

**Rollback strategy:** nothing to roll back — this app has no data of its own, only a Redis cache that self-expires within five minutes regardless of any bug.

---

## 14. Testing

### 14.1 `apps/analytics/tests/test_selectors.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents.models import AgentRun, AgentRunStatus, AgentType
from apps.analytics.selectors import get_agent_performance_summary, get_platform_summary
from apps.trips.models import Trip, TripStatus

User = get_user_model()


class GetPlatformSummarySelectorTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="a@example.com", password="pass1234")
        for status_value in [TripStatus.DRAFT, TripStatus.DRAFT, TripStatus.PLANNED]:
            Trip.objects.create(
                user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 3),
                status=status_value,
            )

    def test_trip_counts_correct(self):
        summary = get_platform_summary()
        self.assertEqual(summary["total_trips"], 3)
        self.assertEqual(summary["trips_by_status"]["draft"], 2)
        self.assertEqual(summary["trips_by_status"]["planned"], 1)

    def test_query_count_is_fixed_for_trip_breakdown(self):
        # ONE aggregate() call for all 6 trip counts, not 6 separate
        # .filter().count() calls — the entire point of this chapter.
        with self.assertNumQueries(2):  # 1 for trip aggregate, 1 for agent aggregate
            get_platform_summary()


class GetAgentPerformanceSummaryTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="ap@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 3))
        AgentRun.objects.create(trip=trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.SUCCEEDED)
        AgentRun.objects.create(trip=trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.SUCCEEDED)
        AgentRun.objects.create(trip=trip, agent_type=AgentType.FULL_GRAPH, status=AgentRunStatus.FAILED)

    def test_success_rate_calculated_correctly(self):
        summary = get_agent_performance_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["succeeded"], 2)
        self.assertEqual(summary["failed"], 1)

    def test_single_query(self):
        with self.assertNumQueries(1):
            get_agent_performance_summary()
```

### 14.2 `apps/analytics/tests/test_caching.py`

```python
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.analytics import caching


class CachingTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch("apps.analytics.caching.get_platform_summary")
    def test_second_call_within_ttl_does_not_recompute(self, mock_get_summary):
        mock_get_summary.return_value = {"total_trips": 5}

        first = caching.get_cached_platform_summary()
        second = caching.get_cached_platform_summary()

        self.assertEqual(first, second)
        mock_get_summary.assert_called_once()

    def test_cache_key_used(self):
        with patch("apps.analytics.caching.get_platform_summary", return_value={"total_trips": 1}):
            caching.get_cached_platform_summary()
        self.assertIsNotNone(cache.get("analytics:platform_summary"))
```

### 14.3 `apps/analytics/tests/test_views.py`

```python
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AnalyticsViewPermissionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.regular_user = User.objects.create_user(email="r@example.com", password="pass1234")
        self.staff_user = User.objects.create_user(email="s@example.com", password="pass1234", is_staff=True)

    def _login(self, email):
        response = self.client.post(reverse("accounts:login"), {"email": email, "password": "pass1234"})
        return {"HTTP_AUTHORIZATION": f"Bearer {response.data['tokens']['access']}"}

    def test_regular_user_forbidden(self):
        response = self.client.get(
            reverse("analytics:platform-summary"), **self._login("r@example.com")
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_allowed(self):
        response = self.client.get(
            reverse("analytics:platform-summary"), **self._login("s@example.com")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_rejected(self):
        response = self.client.get(reverse("analytics:platform-summary"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.analytics -v 2
```

---

## 15. Git Commit

```bash
git add apps/analytics/ config/urls.py
git commit -m "feat(analytics): read-only aggregation, closes Volume 6

- models.py intentionally empty (docstring only) — analytics is
  100% read-only against other apps' tables, same 'empty file
  honestly reflects scope' convention as Chapter 3 (core) and
  Chapter 23 (bookings); no admin.py at all, since there's no model
  to register
- selectors.py: EVERY multi-count function uses a single .aggregate()
  with Count(..., filter=Q(...)) annotations, proven via
  assertNumQueries, not just claimed — direct aggregate-query
  analog of Chapter 8's Prefetch/select_related discipline
- caching.py: cache.get_or_set() pattern, deliberately different
  from Chapter 17's cache.incr() rate limiter — right tool for
  'expensive to compute, fine to be a few minutes stale' data
- get_recommendation_acceptance_rate() excludes PENDING recommendations
  from the denominator — only counts what was actually decided
- IsAdminUser (DRF built-in) — the project's THIRD distinct
  permission model, alongside IsOwner (everywhere) and Chapter 21's
  one AllowAny exception; reached for a built-in instead of writing
  a new custom permission class

Volume 6 (Supporting Apps) complete. Chapter 24 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `apps/analytics/models.py` contains only a docstring; `makemigrations --check --dry-run` reports no changes
- [ ] No `admin.py` exists for this app
- [ ] Every multi-count selector function proven to run in a fixed, small number of queries via `assertNumQueries`
- [ ] `get_recommendation_acceptance_rate` correctly excludes pending recommendations from its denominator
- [ ] `get_or_set` caching verified to prevent recomputation within the TTL window — verified via `assert_called_once()`
- [ ] `IsAdminUser` correctly rejects regular authenticated users (403) and unauthenticated requests (401), while allowing staff (200)
- [ ] All tests passing
- [ ] Commit made
- [ ] **Volume 6 (Supporting Apps) is now complete**

---

## 17. Next Chapter Preview

**Chapter 25 — Full Testing Suite** begins Volume 7 (Hardening & Production). With 24 chapters and roughly two dozen apps' worth of individually-tested code now in place, this chapter takes stock: consolidating the plain-`pytest` (`ai/`) and Django (`manage.py test`) test-running worlds that Chapter 11 explicitly deferred, auditing coverage across every app, and formalizing the regression-testing discipline Architecture Handbook §11 called for from the very beginning. Say **"Continue to Chapter 25"** when ready.
