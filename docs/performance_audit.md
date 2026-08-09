# Performance Audit — Chapter 27

## Scope

This audit was performed against the TraVerse `main` baseline after the Chapter 26 security-hardening merge.

The goal was to identify real query-shape and hot-path gaps without changing code that already has a justified, bounded access pattern.

## Already Proven / Intentionally Unchanged

- `apps.itinerary.selectors.get_trip_itinerary` already uses a `Prefetch` for itinerary items and `select_related("destination")`, with a documented two-query shape independent of itinerary size.
- `apps.analytics.caching` already applies a five-minute `cache.get_or_set()` pattern to the aggregate analytics selectors introduced by Chapter 24.
- `apps.documents.selectors.get_active_document_by_token` already excludes inactive and expired share links correctly; Chapter 27 adds caching around that selector rather than changing its correctness rules.
- Existing destination search remains a single ORM queryset and is not speculatively cached as part of this chapter.

## Gap 1 — Planning Hot Path

### Finding

`_build_initial_state()` consumes `trip.destinations.all()` on every planning execution. The relation itself is a bounded, single-query read, so this is not an N+1 loop. The real risk is that the asynchronous planning worker was loading a plain `Trip` before handing it to the service, leaving the hot-path relation unprefetched.

### Important repository adaptation

The Chapter 27 specification proposes optimizing `TripPlanView` with `select_related()`/`prefetch_related()`. That does **not** work in the current TraVerse architecture because `TripPlanView` only queues a Celery task with `trip_id`; its fetched `Trip` instance is not passed to the worker.

The correct optimization point in the current repository is therefore `apps.ai_agents.tasks.run_travel_planner_task`, where the worker actually constructs the `Trip` instance used by `run_travel_planner()`.

The worker now loads:

- the Trip's `user` relation with `select_related()`;
- the Trip's `destinations` relation with `prefetch_related()`.

This preserves the Chapter 27 intent while applying it at the real query-construction boundary.

## Gap 2 — Public Share-Link Hot Path

### Finding

`get_active_document_by_token()` is used by the public share-link endpoint and previously queried PostgreSQL for every request, including repeated requests for the same invalid or revoked token.

### Fix

`apps.documents.caching.get_cached_active_document()` now provides a short-lived cache around the existing selector.

- Cache key: `documents:active_token:{token}`
- TTL: 60 seconds
- Valid documents are cached directly.
- Invalid/expired/revoked results are cached using the `MISS` sentinel.
- A plain cached `None` is deliberately not used because `cache.get()` cannot distinguish it from an uncached key.

The public share endpoint now uses the cached accessor.

The 60-second TTL is deliberately shorter than Chapter 24's analytics cache. A revoked link can therefore stop being served from this cache within a bounded, short window without introducing a five-minute stale-validity period.

## Combined Planning Baseline

A new performance test wraps the complete `run_travel_planner()` execution, including:

- initial Trip/destination state construction;
- conversation-session lookup;
- destination retrieval;
- AgentRun creation;
- itinerary persistence;
- budget persistence and budget-total synchronization;
- weather persistence;
- recommendation persistence;
- packing-list persistence;
- success notification persistence;
- AgentRun completion update.

The Chapter 27 value of **25 queries is treated as a ceiling, not a target**. The test uses `CaptureQueriesContext` with `assertLessEqual()` semantics because Django's `assertNumQueries()` asserts an exact number rather than a ceiling. This avoids encoding a false requirement that a healthy implementation must execute exactly 25 queries.

Any future change that pushes the complete planning run above 25 queries must be treated as a deliberate performance decision and reviewed rather than silently accepted.

## Worker Query Shape

A dedicated test also verifies that the Celery planning worker performs the intended query shape: one Trip query with the user joined, one prefetch query for destinations, and one initiating-user lookup.

## Cache Test Coverage

The new document-cache tests cover:

1. valid token is cached after the first lookup;
2. repeated valid lookup does not call the selector again;
3. invalid token caches the `MISS` sentinel;
4. repeated invalid lookup does not call the selector again;
5. expired documents are cached as misses;
6. the document cache TTL is exactly 60 seconds.

## No Migration Required

All Chapter 27 changes are query-shape, cache, test, task-loading, and documentation changes. No Django model or schema changes were introduced, so no migration is required.

## Deliberate Non-Changes

This chapter does **not** add caching to every slow-looking selector, does not rewrite existing proven selectors, and does not add speculative indexes. The objective is a measured performance audit, not broad optimization by intuition.
