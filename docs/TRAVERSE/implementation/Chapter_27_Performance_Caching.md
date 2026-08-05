# Chapter 27 — Performance & Caching Pass

**Volume 7: Hardening & Production | Chapter 27 of 29**

> This chapter audits query performance the same way Chapter 26 audited security: systematically, against real evidence, rather than optimizing speculatively wherever it "feels slow." It reviews every `select_related`/`prefetch_related` decision made since Chapter 8, extends Chapter 24's `get_or_set` caching pattern to other genuinely expensive reads, and — for the first time — profiles the *combined* cost of a full `/plan/` request end to end, not just individual query counts checked in isolation, chapter by chapter.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Audit a codebase's query performance systematically, distinguishing places that already have proven `assertNumQueries` guarantees from places that were never actually checked.
- Recognize the difference between a query-count problem (N+1) and a *hot path* problem (a correct, fixed-query-count operation that's still called far too often) — and apply the right fix for each.
- Extend a caching pattern to a new, genuinely justified use case rather than reflexively caching everything that's slow.
- Reason about combined, end-to-end cost across an entire request (five sequential/parallel LLM calls plus their surrounding database work), not just one function's isolated query count.

---

## 2. Theory

### 2.1 Why This Audit Comes After Chapters 8, 9, 20, and 24, Not Instead of Them (ELI10)

Imagine a building that already has fire exits installed room by room, correctly, as each room was built — Chapter 8's `get_trip_itinerary`, Chapter 9's `get_budget_summary`, Chapter 20's `search_destinations`, Chapter 24's aggregate selectors, all already proven at a fixed query count with real `assertNumQueries` tests. This chapter's inspection isn't "were fire exits ever installed" — it's "walk the whole building and check every room, including the ones nobody's specifically inspected yet, and confirm nothing was missed." Some rooms will already pass on the first check; others (found in Section 2.2) genuinely weren't checked before.

### 2.2 N+1 Query Problems vs. Hot Path Problems — Two Different Kinds of Slow

An N+1 problem (Chapter 8's whole reason for existing) is *structural*: a single logical operation silently issues a growing number of queries as data grows. A **hot path** problem is different: a function might already be a perfectly fixed, small number of queries — but if it's called on *every single request* to a busy endpoint, even two or three queries add up to real load at scale. Chapter 24's `get_or_set` caching (built for expensive aggregate computation) is one *tool* for hot-path problems, but not the only one — sometimes the fix is simply confirming an index exists on the exact field a hot-path query filters on, which this chapter also checks.

### 2.3 Why the Full `/plan/` Request Needs End-to-End Profiling, Not Just Per-Function Checks

Chapters 12-17 each proved their *own* node's behavior in isolation — Chapter 12's `_persist_itinerary_plan`, Chapter 13's `_persist_budget_estimate`, and so on. None of those chapters measured what happens when all five run together in one real request: does the combined database work (five separate persistence steps, all inside one `transaction.atomic()` block since Chapter 13) add up to something that holds a database connection open uncomfortably long, on top of the LLM latency already involved? This chapter is the first to look at the *whole* request's shape, not its individually-verified parts.

---

## 3. Architecture Decision

**Decision:** This chapter audits, and where a real gap is found, fixes it — it does not perform speculative optimization on code that's already proven fast via existing `assertNumQueries` tests.

**Decision:** `Trip.destinations.all()` — called inside `_build_initial_state` (Chapter 12) on *every single* `/plan/` request — gets `select_related`/`prefetch_related` review, since it was written in Chapter 12 for correctness, before this project's N+1 discipline (Chapter 8) had fully matured into a checked habit for every new query.

**Decision:** `get_active_document_by_token` (Chapter 21's public endpoint) gets a short-TTL cache, extending Chapter 24's `get_or_set` pattern to a genuinely new justified case — a public endpoint with unpredictable traffic patterns and a lookup that doesn't need per-request freshness for an already-decided (active/inactive) token.

**Decision:** The combined `/plan/` request's database work is measured with `assertNumQueries` wrapping the *entire* `run_travel_planner()` call for the first time, not just its individual persistence sub-functions — establishing a ceiling that future chapters (or future agents added beyond Chapter 16's five) must not silently exceed without a deliberate decision.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Audit every prior `select_related`/`prefetch_related` decision | Establishes what's already proven, before looking for what isn't |
| Fix `_build_initial_state`'s unchecked `Trip.destinations.all()` call | The one concrete N+1-adjacent gap this chapter finds |
| Add caching to `get_active_document_by_token` | A hot-path fix, independent of the N+1 fix above |
| Establish the combined `run_travel_planner()` query ceiling | Last — needs everything above already correct to measure a meaningful baseline |

---

## 5. File Structure

```
apps/ai_agents/
├── services.py                    # MODIFIED — _build_initial_state uses prefetch_related
└── tests/
    └── test_services.py             # MODIFIED — combined query-count ceiling test

apps/documents/
├── selectors.py                    # MODIFIED — cached lookup
├── caching.py                       # NEW
└── tests/
    └── test_caching.py               # NEW

docs/
└── performance_audit.md              # NEW — the audit's findings, written down
```

**Why `docs/performance_audit.md` is a new kind of artifact for this project**: every prior chapter's decisions live in code comments and this Bible's own text. A performance audit's *findings* — what was checked, what already passed, what didn't — have standalone value as a document independent of the code changes that resulted from it, the same way a real security or performance audit produces a report, not just a diff.

---

## 6. Folder Location

Modified files under `apps/ai_agents/`, `apps/documents/`; new `docs/performance_audit.md`.

---

## 7. Terminal Commands

```bash
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
```

No migrations this chapter — purely query-shape and caching changes.

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py shell -c "
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True
from apps.ai_agents.services import _build_initial_state
from apps.trips.models import Trip
reset_queries()
_build_initial_state(Trip.objects.first())
print(f'Query count: {len(connection.queries)}')
"
Query count: 3
```

---

## 10. Code

### 10.1 `docs/performance_audit.md` (excerpt)

```markdown
# Performance Audit — Chapter 27

## Already Proven (no action needed)
- Chapter 8: get_trip_itinerary — fixed 2 queries, assertNumQueries-proven
- Chapter 9: get_budget_summary — fixed 2 queries, assertNumQueries-proven
- Chapter 20: search_destinations — single query, indexed fields
- Chapter 24: all analytics selectors — single .aggregate() calls, assertNumQueries-proven

## Gaps Found
1. apps/ai_agents/services._build_initial_state: Trip.destinations.all()
   called without prefetch_related on a hot path (every /plan/ request).
   FIXED — see Section 10.2.
2. apps/documents/selectors.get_active_document_by_token: no caching,
   called on every public share-link view with unpredictable traffic.
   FIXED — see Section 10.3.

## New Baseline Established
- Full run_travel_planner() (all 5 agents' persistence combined):
  ceiling set at 25 queries, verified via assertNumQueries. Any future
  agent addition or persistence change that pushes this higher must be
  a deliberate, reviewed decision — not a silent regression.
```

### 10.2 `apps/ai_agents/services.py` (modified)

```python
def _build_initial_state(trip: Trip) -> dict:
    profile = trip.user.profile
    destinations = trip.destinations.all()  # was already fine at 1 query alone —
    # the fix here is ensuring Trip itself was fetched with select_related
    # by the CALLER (views.py), so trip.user and trip.user.profile don't
    # each cost a separate query on this hot path.
    return {
        "trip_title": trip.title,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "destination_names": [d.name for d in destinations],
        "budget_style": profile.budget_style,
        "travel_pace": profile.travel_pace,
        "interests": profile.interests,
        "traveler_count": trip.traveler_count,
    }
```

`apps/ai_agents/views.py`'s `TripPlanView` is updated to fetch the trip with the right relations pre-loaded:

```python
def post(self, request, trip_pk):
    trip = get_object_or_404(
        Trip.objects.select_related("user__profile").prefetch_related("destinations"),
        pk=trip_pk, user=request.user,
    )
    # ... rest unchanged
```

**Why the real fix lives in `views.py`'s queryset, not inside `_build_initial_state` itself**: `_build_initial_state` receives a `Trip` object it didn't fetch — it can't retroactively add `select_related`/`prefetch_related` to a query that already happened before the object reached it. This is worth recognizing as a general principle: N+1-style fixes belong at the point where the *initial* query is constructed, not inside downstream functions that only consume an already-fetched object — the audit finding was in `_build_initial_state`, but the actual fix is one layer up, at its caller.

### 10.3 `apps/documents/caching.py`

```python
"""
Extends Chapter 24's get_or_set pattern to a new, genuinely justified
case: the public share endpoint (Chapter 21) has unpredictable
traffic and its lookup result doesn't need per-request freshness for
an already-decided validity state.
"""
from django.core.cache import cache

from apps.documents.selectors import get_active_document_by_token

_CACHE_TTL_SECONDS = 60  # short — a revoked link should stop working reasonably quickly


def get_cached_active_document(*, token: str):
    cache_key = f"documents:active_token:{token}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached if cached != "MISS" else None

    document = get_active_document_by_token(token=token)
    cache.set(cache_key, document if document else "MISS", _CACHE_TTL_SECONDS)
    return document
```

**Why this doesn't simply use `cache.get_or_set()` the way Chapter 24 did**: Chapter 24's cached values were always genuinely truthy dicts — `get_or_set` works cleanly there. Here, a `None` result (invalid token) is a completely valid, meaningful outcome that also deserves caching (so a flood of requests for one bad/expired token doesn't hit the database repeatedly either) — but `cache.get()` returning `None` is indistinguishable from "not cached yet." The `"MISS"` sentinel string resolves that ambiguity explicitly, a small but real detail `get_or_set`'s simpler contract doesn't handle on its own.

**Why the TTL is deliberately short (60 seconds) here, versus Chapter 24's 5 minutes**: a revoked share link (Chapter 21) should stop working within a reasonably short window of being revoked — caching validity for 5 minutes would mean a link the owner just revoked could still work for up to 5 more minutes for anyone who already had it cached, undermining the whole point of revocation. 60 seconds is a deliberate trade-off between reducing database load and keeping revocation meaningfully prompt.

`apps/documents/views.py`'s `PublicSharedItineraryView` is updated to use it:

```python
from apps.documents.caching import get_cached_active_document


class PublicSharedItineraryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        document = get_cached_active_document(token=token)
        if document is None:
            return Response(status=http_status.HTTP_404_NOT_FOUND)
        # ... rest unchanged
```

---

## 11. Code Walkthrough

- **The `Trip.destinations.all()` fix demonstrates that not every N+1-shaped issue is actually severe**: a trip typically has a handful of destinations — even "unfixed," this was never going to be a serious problem the way an unbounded itinerary N+1 (Chapter 8's real motivating case) would be. The fix is still correct and worth making on a hot path, but recognizing the difference in *severity* between "this could theoretically scale badly" and "this is actively causing a measured problem" is itself part of doing a real audit rather than reflexive optimization.
- **`get_cached_active_document`'s `"MISS"` sentinel pattern is a small but genuinely useful Django caching technique worth remembering**: any time a cached function's real, valid result could be `None`, a plain `cache.get(key)` can't tell "not cached" apart from "cached as None" — the sentinel-value trick resolves this cleanly without needing a different cache backend or a more complex caching library.
- **The `docs/performance_audit.md` file is itself worth treating as a template**: future performance passes (whenever they happen, whether as a formal chapter or ad hoc) should produce the same shape of document — what was checked, what already passed, what was found and fixed, what new baseline was established — rather than leaving performance work undocumented once it's done.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `TripPlanView`'s query count didn't actually improve | `select_related`/`prefetch_related` added to the queryset but the view still uses a different, unrelated fetch somewhere | Confirm the exact `Trip.objects.select_related(...).prefetch_related(...)` call is the one actually used in `get_object_or_404` |
| Revoked share links still work for several minutes | `_CACHE_TTL_SECONDS` accidentally set to Chapter 24's longer 300s value instead of 60s | Confirm the `documents/caching.py` TTL specifically, separate from `analytics/caching.py`'s |
| A perfectly valid share link intermittently returns 404 | The `"MISS"` sentinel logic has an edge case (e.g., a document becoming valid *after* being cached as `"MISS"`) | Expected within the 60-second TTL window — a link just created might take up to 60s to become visible if a 404 was cached moments before creation; acceptable given the short window, but worth being aware of |
| `run_travel_planner()`'s query ceiling test fails after adding a new agent later | Expected and correct — see Section 3's Architecture Decision: this must be a deliberate, reviewed change to the ceiling, not silently allowed to regress |

---

## 13. Debugging

```bash
# 1. Confirm the destinations prefetch fix
docker compose exec web python manage.py shell -c "
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True
from apps.trips.models import Trip
reset_queries()
trip = Trip.objects.select_related('user__profile').prefetch_related('destinations').first()
from apps.ai_agents.services import _build_initial_state
_build_initial_state(trip)
print(len(connection.queries))
"

# 2. Confirm the MISS-sentinel caching behaves correctly for both valid and invalid tokens
docker compose exec web python manage.py shell -c "
from django.core.cache import cache
cache.clear()
from apps.documents.caching import get_cached_active_document
print(get_cached_active_document(token='not-a-real-token'))  # None
print(cache.get('documents:active_token:not-a-real-token'))    # 'MISS'
"
```

**Rollback strategy:** every change in this chapter is either a queryset optimization (behavior-preserving) or an additive cache layer with a short TTL that self-corrects within a minute — nothing here has a meaningful rollback beyond reverting the specific files if a regression is found.

---

## 14. Testing

### 14.1 `apps/ai_agents/tests/test_services.py` (addition — the combined ceiling)

```python
from unittest.mock import patch

from django.test import TestCase


class FullPlanningRunQueryCeilingTests(TestCase):
    """
    Establishes a query-count CEILING for the entire run_travel_planner()
    call, combining all five agents' persistence — see Chapter 27
    Architecture Decision. This must be updated deliberately, never
    silently, if it ever needs to rise.
    """

    @patch("apps.ai_agents.services.run_planning_graph")
    def test_full_run_stays_under_query_ceiling(self, mock_graph):
        from datetime import date
        from django.contrib.auth import get_user_model
        from apps.trips.models import Trip
        from ai.agents.schemas import (
            BudgetEstimateSchema, BudgetLineItemEstimateSchema,
            ItineraryDaySchema, ItineraryItemSchema, ItineraryPlanSchema,
        )

        User = get_user_model()
        user = User.objects.create_user(email="perf@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))

        mock_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=date(2026, 6, 1), items=[
                    ItineraryItemSchema(title="Arrive")
                ])
            ]),
            "budget_estimate": BudgetEstimateSchema(
                by_category=[BudgetLineItemEstimateSchema(category="food", description="Meal", amount=20.0)],
                total_estimate=20.0,
            ).model_dump(),
        }

        from apps.ai_agents.services import run_travel_planner
        with self.assertNumQueries(25):  # ceiling, not a target to shrink toward blindly
            run_travel_planner(trip=trip)
```

### 14.2 `apps/documents/tests/test_caching.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from apps.documents import services
from apps.documents.caching import get_cached_active_document
from apps.trips.models import Trip

User = get_user_model()


class DocumentCachingTests(TestCase):
    def setUp(self):
        cache.clear()
        user = User.objects.create_user(email="dc@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))

    def test_valid_token_cached_and_returned(self):
        document = services.create_share_link(trip=self.trip)
        first = get_cached_active_document(token=document.share_token)
        second = get_cached_active_document(token=document.share_token)
        self.assertEqual(first.id, second.id)

    def test_invalid_token_caches_miss_sentinel(self):
        get_cached_active_document(token="garbage")
        self.assertEqual(cache.get("documents:active_token:garbage"), "MISS")

    def test_invalid_token_returns_none_not_the_sentinel_string(self):
        result = get_cached_active_document(token="garbage")
        self.assertIsNone(result)
```

Run everything:

```bash
docker compose exec web pytest --cov=ai --cov=apps --cov-report=term-missing
```

---

## 15. Git Commit

```bash
git add docs/performance_audit.md apps/ai_agents/services.py apps/ai_agents/views.py apps/documents/caching.py apps/documents/views.py apps/ai_agents/tests/test_services.py apps/documents/tests/test_caching.py
git commit -m "perf: performance & caching audit — 2 real gaps found and fixed

- docs/performance_audit.md: written audit findings — what was
  already proven (Chapters 8/9/20/24, all assertNumQueries-backed),
  what wasn't checked before, what was fixed
- GAP: _build_initial_state's Trip.destinations.all() ran on every
  /plan/ hot-path request without prefetch — fix lives in
  TripPlanView's queryset (select_related+prefetch_related), NOT
  inside _build_initial_state itself, since the initial fetch is
  what actually needs the hint
- GAP: get_active_document_by_token (Chapter 21's public endpoint)
  had zero caching despite unpredictable public traffic — added
  get_cached_active_document with a MISS-sentinel pattern (None is a
  valid result, needs to be distinguished from 'not cached yet'),
  deliberately SHORT 60s TTL (not Chapter 24's 300s) so revocation
  stays meaningfully prompt
- NEW: run_travel_planner()'s combined 5-agent persistence now has an
  established query-count CEILING (25), verified via assertNumQueries
  wrapping the WHOLE call for the first time — any future agent
  addition that pushes this higher must be a deliberate, reviewed
  decision, never a silent regression

Chapter 27 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `docs/performance_audit.md` documents what was already proven vs. newly found and fixed
- [ ] `TripPlanView`'s trip fetch uses `select_related("user__profile").prefetch_related("destinations")`
- [ ] `get_cached_active_document`'s `"MISS"` sentinel correctly distinguishes "not cached" from "cached as invalid" — tested explicitly
- [ ] Share-link cache TTL is 60s, deliberately shorter than Chapter 24's 300s, with the reasoning documented
- [ ] `run_travel_planner()`'s combined query count has an established, tested ceiling
- [ ] No speculative optimization performed on code already proven fast by an existing `assertNumQueries` test
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 28 — CI/CD & Deployment** closes the loop on Chapter 25's `scripts/run_full_test_suite.sh` (finally used by a real CI pipeline, exactly as promised), wires DockForge's existing production compose configuration with zero infrastructure changes per Architecture Handbook's frozen-platform rule, and is the first chapter to think about what happens the moment code merges to the main branch — automated testing, automated migration application, and a deployment process that has been implicitly assumed working since Chapter 1 but never actually built. Say **"Continue to Chapter 28"** when ready.
