# Chapter 8 — `itinerary` App: Day-by-Day Planning

**Volume 3: Trip Sub-Domains | Chapter 8 of 29**

> This is the first two-level parent-child relationship in the project: `ItineraryDay` belongs to `Trip`, and `ItineraryItem` belongs to `ItineraryDay`. It's also the first place explicit ordering matters — items within a day have a real sequence a user cares about — and the first chapter where getting the query pattern wrong silently creates a serious N+1 performance problem instead of a loud error. Everything here is still hand-authored (no AI yet); Chapter 12's Travel Planner Agent will *populate* these same models, not replace them.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Model a two-level nested parent-child relationship (`Trip` → `ItineraryDay` → `ItineraryItem`) with correct cascade behavior at each level.
- Implement explicit, gap-tolerant ordering (an `order` integer field) and a service function that reorders items safely.
- Recognize an N+1 query before it happens, and use `prefetch_related` with `Prefetch` objects to fetch two levels of nested relations in a fixed, small number of queries regardless of trip size.
- Nest serializers correctly (day → items) for both read and write, and understand why bulk nested writes need more care than bulk nested reads.

---

## 2. Theory

### 2.1 Why Two Levels, Not One Flat `ItineraryItem` With a `day_number` Integer (ELI10)

Imagine a school binder. You could either have one giant pile of loose worksheets each labeled "Monday" or "Tuesday" (a flat model), or you could have labeled dividers for each day, with worksheets filed behind the right divider (two levels). The divider approach makes "give me everything for Tuesday" a direct lookup, lets each day carry its own metadata later (a day-level summary, weather forecast — Chapter 14's Weather Agent output lands exactly here), and matches how Architecture Handbook §5.2 already modeled it: `ItineraryDay` and `ItineraryItem` are separate entities, not one flat table with a date column.

### 2.2 What N+1 Actually Means (ELI10)

Imagine asking "what's in your backpack?" to 30 kids, one at a time, instead of asking the teacher once for the whole class list with backpacks already itemized. Django's ORM, if you're not careful, does exactly the "ask each kid individually" thing: fetch 1 query for all `ItineraryDay`s, then a *separate* query for each day's items (N more queries) — for a 14-day trip, that's 15 queries instead of 2. This is invisible in development with 3 test days and devastating in production with real trip sizes; catching it now, while it's cheap to fix, is the entire point of this section of the chapter.

### 2.3 Why Ordering Uses an Integer Field With Gaps, Not a Tight 0,1,2,3 Sequence

If item ordering is stored as a strict 0,1,2,3... sequence, inserting a new item between position 1 and 2 requires renumbering every item after it. Storing order values with gaps (10, 20, 30...) lets a new item be inserted at 15 without touching any other row — a classic, low-tech but effective technique, revisited fully in Section 15.

---

## 3. Architecture Decision

**Decision:** `ItineraryDay.trip` and `ItineraryItem.day` both use `on_delete=CASCADE`.

**Why:** unlike `ItineraryItem.destination` (Section 10.1, `SET_NULL`), a day/item genuinely has no meaning independent of its trip — Architecture Handbook §5.8 already established this exact reasoning for `BudgetLineItem.budget`, and the same logic applies one level up here.

**Decision:** Order values are stored as multiples of 10 (`10, 20, 30, ...`), with a service function that renumbers the whole day only when gaps are fully exhausted, not on every insert.

**Alternative considered:** Use a `PositionField`-style third-party package. **Rejected because:** the gap-based approach is simple enough to hand-write, fully transparent (no hidden magic to debug), and avoids adding a dependency for a genuinely small amount of logic — consistent with the YAGNI stance already taken on `django-filter` in Chapter 6.

**Decision:** `ItineraryDay` is fetched with `Prefetch("items", queryset=ItineraryItem.objects.order_by("order"))` rather than relying on the item model's default `Meta.ordering`.

**Trade-off documented:** this means ordering is specified in two places conceptually (the model's default `Meta.ordering` for convenience elsewhere, and an explicit `Prefetch` queryset for the API's exact needs) — accepted because the API's serialized "items in day order" contract must never silently break if someone changes `Meta.ordering` for an unrelated reason later; the `Prefetch` queryset makes the ordering used in the API response explicit and independent of that model default.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `ItineraryDay` | Needs `Trip` (Ch.7) to exist |
| Define `ItineraryItem` | Needs `ItineraryDay` (this chapter, same file) and optionally `Destination` (Ch.6) |
| Write the ordering service functions | Must exist before any view lets a client reorder items, or ordering bugs get baked into the API contract |
| Write the N+1-safe queryset helper | Must exist before the view is built, so the view is correct from its very first version, not "fixed later" |
| Write nested serializers | Needs the queryset helper's shape decided first, since nested read serializers mirror it |

---

## 5. File Structure

```
apps/itinerary/
├── __init__.py
├── apps.py
├── models.py
├── services.py               # ordering logic: add_item, reorder_items, renumber_day
├── selectors.py                # NEW pattern — read-optimized queries live here, separate from services.py
├── serializers.py
├── permissions.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    └── test_views.py
```

**Why `selectors.py` is introduced as a new, separate pattern from `services.py` starting this chapter:** `services.py` (Chapter 7) is about **writes and business rules**. `selectors.py` is about **reads optimized for a specific consumer's needs** — in this case, "give me a trip's itinerary with days and items prefetched in exactly the right order, in a fixed small number of queries." Mixing this query-shaping concern into `services.py` would blur two very different responsibilities (validating business rules vs. optimizing database access patterns); splitting them is a common, deliberate Django enterprise convention, listed explicitly in the Implementation Bible's per-app file list.

---

## 6. Folder Location

All new files under `apps/itinerary/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations itinerary
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.itinerary
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations itinerary
Migrations for 'itinerary':
  apps/itinerary/migrations/0001_initial.py
    - Create model ItineraryDay
    - Create model ItineraryItem

$ curl http://localhost:8000/api/v1/trips/<trip_id>/itinerary/ -H "Authorization: Bearer <access>"
{
  "days": [
    {
      "id": 1, "date": "2026-10-01", "day_number": 1,
      "items": [
        {"id": 5, "order": 10, "title": "Arrive, check into hotel", "start_time": "14:00"},
        {"id": 6, "order": 20, "title": "Explore Shibuya", "start_time": "17:00"}
      ]
    }
  ]
}
```

---

## 10. Code

### 10.1 `apps/itinerary/models.py`

```python
from django.db import models

from apps.core.models import TimeStampedModel


class ItineraryDay(TimeStampedModel):
    """
    One day of a trip's itinerary. Belongs to exactly one Trip.
    """
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="itinerary_days",
    )
    date = models.DateField()
    day_number = models.PositiveSmallIntegerField(
        help_text="1-indexed day of the trip, kept denormalized alongside `date` "
                   "for fast display without recomputing from trip.start_date every time.",
    )
    summary = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["day_number"]
        constraints = [
            models.UniqueConstraint(fields=["trip", "day_number"], name="unique_day_number_per_trip"),
            models.UniqueConstraint(fields=["trip", "date"], name="unique_date_per_trip"),
        ]
        verbose_name = "Itinerary Day"
        verbose_name_plural = "Itinerary Days"

    def __str__(self) -> str:
        return f"{self.trip.title} — Day {self.day_number}"


class ItineraryItem(TimeStampedModel):
    """
    A single activity within a day. Belongs to exactly one
    ItineraryDay. Optionally references a Destination (a specific
    point of interest) — this is the fine-grained, per-day
    destination association that Chapter 7's ADR deliberately
    deferred out of Trip.destinations.
    """
    day = models.ForeignKey(
        ItineraryDay, on_delete=models.CASCADE, related_name="items",
    )
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="itinerary_items",
        help_text="Optional. SET_NULL, not CASCADE — deactivating/removing a "
                   "destination must never destroy a user's itinerary item.",
    )
    order = models.PositiveIntegerField(default=10)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.TimeField(null=True, blank=True)
    estimated_cost_usd = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_ai_generated = models.BooleanField(
        default=False,
        help_text="True for items created by Chapter 12's Travel Planner Agent, "
                   "False for items a user added/edited by hand. Lets the API and "
                   "UI distinguish 'AI suggested this' from 'you added this'.",
    )

    class Meta:
        ordering = ["order"]
        indexes = [
            models.Index(fields=["day", "order"]),
        ]
        verbose_name = "Itinerary Item"
        verbose_name_plural = "Itinerary Items"

    def __str__(self) -> str:
        return f"{self.title} ({self.day})"
```

**Why `day_number` is stored on `ItineraryDay` even though it's technically derivable from `date - trip.start_date`:** this is a deliberate, small, documented denormalization (the same class of trade-off as `Trip.computed_budget_total` in Chapter 7 / Architecture Handbook ADR-7) — computing it on every serialization would mean every day row needs to join back to its trip's `start_date` just to render a label, for a value that never changes once the day is created. The `UniqueConstraint` on `(trip, day_number)` guards against it ever drifting out of sync with reality.

**Why `is_ai_generated` is added now, even though no AI agent exists until Chapter 12:** waiting until Chapter 12 to add this field would mean either a disruptive migration on a model already holding real hand-created data, or the AI agent silently indistinguishable from manual entries. Adding the field now, defaulting to `False`, costs nothing today and saves a painful retrofit three chapters from now — a small forward-looking design decision explicitly flagged rather than silently smuggled in.

### 10.2 `apps/itinerary/services.py`

```python
"""
Write-side business logic for itinerary days/items, including the
gap-based ordering scheme described in Chapter 8 Theory §2.3.
"""
from apps.core.exceptions import BusinessRuleViolation
from apps.itinerary.models import ItineraryDay, ItineraryItem

_ORDER_GAP = 10


class NoRoomToInsert(BusinessRuleViolation):
    default_message = "No ordering gap available; the day needs renumbering."
    default_code = "no_room_to_insert"


def add_item_to_day(*, day: ItineraryDay, title: str, **extra_fields) -> ItineraryItem:
    last_item = day.items.order_by("-order").first()
    next_order = (last_item.order + _ORDER_GAP) if last_item else _ORDER_GAP
    return ItineraryItem.objects.create(day=day, title=title, order=next_order, **extra_fields)


def insert_item_between(*, day: ItineraryDay, title: str, before: ItineraryItem,
                         after: ItineraryItem, **extra_fields) -> ItineraryItem:
    gap = after.order - before.order
    if gap <= 1:
        renumber_day(day=day)
        before.refresh_from_db()
        after.refresh_from_db()
        gap = after.order - before.order

    new_order = before.order + gap // 2
    return ItineraryItem.objects.create(day=day, title=title, order=new_order, **extra_fields)


def renumber_day(*, day: ItineraryDay) -> None:
    """
    Resets every item in a day to a clean 10, 20, 30... sequence.
    Only called when gaps are exhausted — not on every write, per
    Chapter 8 Architecture Decision.
    """
    items = list(day.items.order_by("order"))
    for index, item in enumerate(items, start=1):
        item.order = index * _ORDER_GAP
    ItineraryItem.objects.bulk_update(items, ["order"])
```

**Why `insert_item_between` recalculates using integer floor division (`gap // 2`) instead of always renumbering**: this is the entire point of the gap-based scheme — most inserts (the common case) need zero writes to any *other* row, only the new row itself. Renumbering is the fallback path, triggered only when two adjacent items' order values are already consecutive integers (`gap <= 1`) and there is no room left between them.

**Why `bulk_update` is used in `renumber_day`, not a loop of individual `.save()` calls:** this is the direct fix for the N+1 problem, applied on the *write* side this time — updating 20 items individually would be 20 separate `UPDATE` statements; `bulk_update` issues a single, efficient batched statement.

### 10.3 `apps/itinerary/selectors.py`

```python
"""
Read-optimized queries for the itinerary app. Every function here
returns data shaped for a specific known consumer, with query count
kept fixed and small regardless of trip size — see Chapter 8 Theory
§2.2 on N+1 queries.
"""
from django.db.models import Prefetch

from apps.itinerary.models import ItineraryDay, ItineraryItem


def get_trip_itinerary(*, trip) -> list[ItineraryDay]:
    """
    Returns every day of a trip, each with its items already
    prefetched in the correct order, in exactly 2 queries total
    (1 for days, 1 for all items across all days) — NOT 1 + N.
    """
    items_prefetch = Prefetch(
        "items",
        queryset=ItineraryItem.objects.select_related("destination").order_by("order"),
    )
    return list(
        trip.itinerary_days
        .prefetch_related(items_prefetch)
        .order_by("day_number")
    )
```

**Why `select_related("destination")` is chained inside the `Prefetch` queryset, not applied separately**: `select_related` (a SQL JOIN, for forward foreign keys) and `prefetch_related` (a separate query, for reverse/M2M relations) solve different problems and are frequently confused. Here, `items` needs `prefetch_related` (many items per day, a reverse FK), but each individual item's `destination` is a *forward* FK, best resolved with a JOIN via `select_related` — nesting them this way means a full 2-level fetch touching three tables (`ItineraryDay`, `ItineraryItem`, `Destination`) still costs only 2 database round-trips, not 3, and never scales with the number of items.

### 10.4 `apps/itinerary/serializers.py`

```python
from rest_framework import serializers

from apps.destinations.serializers import DestinationSerializer
from apps.itinerary.models import ItineraryDay, ItineraryItem


class ItineraryItemSerializer(serializers.ModelSerializer):
    destination = DestinationSerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        source="destination", write_only=True, required=False, allow_null=True,
        queryset=None,  # set in __init__ to avoid a circular import at module load time
    )

    class Meta:
        model = ItineraryItem
        fields = [
            "id", "order", "title", "description", "start_time",
            "estimated_cost_usd", "is_ai_generated", "destination", "destination_id",
        ]
        read_only_fields = ["id", "order", "is_ai_generated"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.destinations.models import Destination
        self.fields["destination_id"].queryset = Destination.objects.filter(is_active=True)


class ItineraryDaySerializer(serializers.ModelSerializer):
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = ["id", "date", "day_number", "summary", "items"]
        read_only_fields = ["id", "day_number"]


class AddItineraryItemSerializer(serializers.Serializer):
    """
    Separate, minimal serializer for the "add item" write endpoint —
    deliberately not reusing ItineraryItemSerializer for writes,
    since order is service-assigned, never client-supplied (see
    views.py — order is intentionally absent from this serializer).
    """
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    start_time = serializers.TimeField(required=False, allow_null=True)
    estimated_cost_usd = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True,
    )
    destination_id = serializers.IntegerField(required=False, allow_null=True)
```

**Why `order` is entirely absent from `AddItineraryItemSerializer`**: this mirrors Chapter 7's decision to keep `status` off the general `TripSerializer` writable fields — ordering is assigned exclusively by `services.add_item_to_day()`/`insert_item_between()`, never accepted directly from client input, preventing a client from ever creating two items with a colliding or out-of-sequence order value by mistake.

### 10.5 `apps/itinerary/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.itinerary import selectors, services
from apps.itinerary.models import ItineraryDay, ItineraryItem
from apps.itinerary.serializers import AddItineraryItemSerializer, ItineraryDaySerializer
from apps.trips.models import Trip


class TripItineraryView(APIView):
    """
    Read the full itinerary for a trip. Ownership is enforced via
    the trip lookup itself — a trip belonging to someone else simply
    will not be found for this user (see get_trip_for_user below),
    returning 404, consistent with itinerary being reached only
    THROUGH a trip, never addressed by its own independent ID in
    this endpoint's URL.
    """
    permission_classes = [IsAuthenticated]

    def get_trip_for_user(self, pk, user):
        return get_object_or_404(Trip, pk=pk, user=user)

    def get(self, request, trip_pk):
        trip = self.get_trip_for_user(trip_pk, request.user)
        days = selectors.get_trip_itinerary(trip=trip)
        return Response({"days": ItineraryDaySerializer(days, many=True).data})


class AddItineraryItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk, day_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        day = get_object_or_404(ItineraryDay, pk=day_pk, trip=trip)

        serializer = AddItineraryItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        destination_id = data.pop("destination_id", None)

        item = services.add_item_to_day(
            day=day, destination_id=destination_id, **data,
        )
        from apps.itinerary.serializers import ItineraryItemSerializer
        return Response(ItineraryItemSerializer(item).data, status=http_status.HTTP_201_CREATED)
```

**Why `TripItineraryView.get_trip_for_user` filters `Trip.objects.get(pk=pk, user=user)` rather than fetching the trip first and applying `IsOwner` afterward**: unlike Chapter 7's `TripDetailView` (which deliberately returns 403 for a trip that exists but isn't yours, per Chapter 3's `ResourceNotOwned` reasoning), here we return a plain 404 instead, because this endpoint's "resource" is *the itinerary*, not the trip directly — from the itinerary endpoint's point of view, a trip that isn't yours legitimately does not exist. This is a deliberate, documented inconsistency with Chapter 7's approach, not an oversight — worth flagging exactly here so it's understood as a choice.

### 10.6 `apps/itinerary/urls.py`

```python
from django.urls import path

from apps.itinerary.views import AddItineraryItemView, TripItineraryView

app_name = "itinerary"

urlpatterns = [
    path("<uuid:trip_pk>/itinerary/", TripItineraryView.as_view(), name="trip-itinerary"),
    path("<uuid:trip_pk>/itinerary/days/<int:day_pk>/items/",
         AddItineraryItemView.as_view(), name="add-item"),
]
```

### 10.7 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.itinerary.urls")),
```

**Why this shares the `api/v1/trips/` prefix with Chapter 7's trip URLs instead of getting its own `api/v1/itinerary/` prefix**: itinerary is always accessed *through* a trip (Architecture Handbook §7.2's page flow: Trip Details → Generated Itinerary), never independently — the URL structure should mirror that nesting rather than implying itinerary is a top-level, independently-addressable resource.

### 10.8 `apps/itinerary/admin.py`

```python
from django.contrib import admin

from apps.itinerary.models import ItineraryDay, ItineraryItem


class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 0
    ordering = ["order"]
    fields = ["order", "title", "start_time", "is_ai_generated"]


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ["trip", "day_number", "date"]
    list_filter = ["date"]
    search_fields = ["trip__title"]
    inlines = [ItineraryItemInline]
```

---

## 11. Code Walkthrough

- **`get_trip_itinerary()` returns exactly 2 queries for a trip of any size**: this is verified directly in Section 14's tests using Django's `assertNumQueries` — not just claimed in a docstring, but proven by an automated test that would fail immediately if a future edit accidentally reintroduces N+1 behavior.
- **`insert_item_between` vs. `add_item_to_day`**: two different service functions for two different real needs — appending to the end of a day (common, cheap) versus inserting between two specific existing items (less common, needs the gap-halving logic). Keeping them separate, rather than one function with a branchy "if position given, do X, else Y" body, keeps each function's logic simple enough to reason about and test independently.
- **`ItineraryItemSerializer.__init__` sets `destination_id`'s queryset dynamically inside `__init__` rather than at class-definition time**: importing `Destination` at module level in `itinerary/serializers.py` while `destinations/serializers.py` might (in a more tangled codebase) import something from `itinerary` back would risk a circular import. Deferring the import to inside `__init__` (which only runs when a serializer instance is actually created, well after all modules have finished loading) is a standard, safe pattern for breaking that kind of risk — used here defensively even though no actual circular import exists yet, because it costs nothing and prevents a future one.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `django.db.utils.IntegrityError` on `unique_day_number_per_trip` | Tried to create two `ItineraryDay`s with the same `day_number` for one trip | Expected — this constraint is doing its job; check the calling code's day-numbering logic |
| Itinerary items appear in the wrong order in the API response | Relying on `Meta.ordering` alone instead of the explicit `Prefetch` queryset ordering | Confirm `selectors.get_trip_itinerary()` is what's actually being called, not a raw `trip.itinerary_days.all()` |
| Test suite passes but production is slow on large trips | N+1 query slipped past review because a small test dataset (2-3 items) didn't reveal it | This is exactly why Section 14 tests query *count*, not just query *correctness* — always assert `assertNumQueries` on any new nested-relation endpoint |
| `404` on `AddItineraryItemView` even though the day exists | `day_pk` belongs to a different trip than `trip_pk` in the URL | This is correct, intentional behavior — the view filters `ItineraryDay.objects.get(pk=day_pk, trip=trip)`, preventing a client from adding an item to a day under the wrong trip |

---

## 13. Debugging

```bash
# 1. Prove the itinerary fetch is really 2 queries, not 1+N, directly in the shell
docker compose exec web python manage.py shell -c "
from django.db import connection, reset_queries
from django.conf import settings
settings.DEBUG = True
reset_queries()
from apps.itinerary import selectors
from apps.trips.models import Trip
trip = Trip.objects.first()
days = selectors.get_trip_itinerary(trip=trip)
[list(d.items.all()) for d in days]  # force evaluation
print(f'Query count: {len(connection.queries)}')
"

# 2. Inspect the actual order values stored for a day (spot-check the gap scheme)
docker compose exec web python manage.py shell -c "
from apps.itinerary.models import ItineraryDay
day = ItineraryDay.objects.first()
print(list(day.items.order_by('order').values_list('order', 'title')))
"
```

**Rollback strategy:** if `renumber_day()` is ever found to have a bug that scrambles an existing day's order, the fix is straightforward precisely *because* order is just an integer field with no other data dependent on its exact value — re-run `renumber_day()` after fixing the bug, and the sequence self-heals to clean `10, 20, 30...` values with no data loss, since item *identity* (each item's own row) was never touched, only the `order` field.

---

## 14. Testing

### 14.1 `apps/itinerary/tests/test_services.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.itinerary import services
from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip

User = get_user_model()


class AddItemToDayServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="i@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        self.day = ItineraryDay.objects.create(trip=trip, date=date(2026, 1, 1), day_number=1)

    def test_first_item_gets_order_10(self):
        item = services.add_item_to_day(day=self.day, title="First")
        self.assertEqual(item.order, 10)

    def test_second_item_gets_order_20(self):
        services.add_item_to_day(day=self.day, title="First")
        second = services.add_item_to_day(day=self.day, title="Second")
        self.assertEqual(second.order, 20)


class InsertItemBetweenServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="i2@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        self.day = ItineraryDay.objects.create(trip=trip, date=date(2026, 1, 1), day_number=1)
        self.first = services.add_item_to_day(day=self.day, title="First")   # order 10
        self.second = services.add_item_to_day(day=self.day, title="Second")  # order 20

    def test_insert_between_uses_gap(self):
        middle = services.insert_item_between(
            day=self.day, title="Middle", before=self.first, after=self.second
        )
        self.assertEqual(middle.order, 15)

    def test_insert_triggers_renumber_when_gap_exhausted(self):
        # Manually collapse the gap to simulate exhaustion
        self.second.order = self.first.order + 1
        self.second.save()
        middle = services.insert_item_between(
            day=self.day, title="Squeezed In", before=self.first, after=self.second
        )
        orders = list(self.day.items.order_by("order").values_list("order", flat=True))
        self.assertEqual(len(orders), len(set(orders)))  # no duplicates after renumber
        self.assertIn(middle.order, orders)


class RenumberDayServiceTests(TestCase):
    def test_renumber_produces_clean_sequence(self):
        user = User.objects.create_user(email="i3@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        day = ItineraryDay.objects.create(trip=trip, date=date(2026, 1, 1), day_number=1)
        for i, weird_order in enumerate([5, 6, 100]):
            item = services.add_item_to_day(day=day, title=f"Item {i}")
            item.order = weird_order
            item.save()

        services.renumber_day(day=day)
        orders = list(day.items.order_by("order").values_list("order", flat=True))
        self.assertEqual(orders, [10, 20, 30])
```

### 14.2 `apps/itinerary/tests/test_selectors.py` (the N+1 proof)

```python
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.itinerary import services
from apps.itinerary.models import ItineraryDay
from apps.itinerary.selectors import get_trip_itinerary
from apps.trips.models import Trip

User = get_user_model()


class GetTripItinerarySelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="sel@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.user, title="Big Trip", start_date=date(2026, 1, 1), end_date=date(2026, 1, 14)
        )
        # 14 days, 3 items each — deliberately large enough that N+1 would be obviously slow
        for day_num in range(1, 15):
            day = ItineraryDay.objects.create(
                trip=self.trip, date=date(2026, 1, day_num), day_number=day_num,
            )
            for _ in range(3):
                services.add_item_to_day(day=day, title="Activity")

    def test_returns_all_days_in_order(self):
        days = get_trip_itinerary(trip=self.trip)
        self.assertEqual(len(days), 14)
        self.assertEqual([d.day_number for d in days], list(range(1, 15)))

    def test_query_count_is_fixed_regardless_of_trip_size(self):
        # 1 query for days, 1 query for all items across all days = 2 total,
        # NOT 1 + 14 (one per day) which is what naive access would cause.
        with self.assertNumQueries(2):
            days = get_trip_itinerary(trip=self.trip)
            for day in days:
                list(day.items.all())  # force evaluation of the prefetch

    def test_items_within_each_day_are_ordered(self):
        days = get_trip_itinerary(trip=self.trip)
        first_day_orders = [item.order for item in days[0].items.all()]
        self.assertEqual(first_day_orders, sorted(first_day_orders))
```

### 14.3 `apps/itinerary/tests/test_views.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.itinerary.models import ItineraryDay
from apps.trips.models import Trip

User = get_user_model()


class TripItineraryViewTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.stranger = User.objects.create_user(email="stranger@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.owner, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 3)
        )
        self.day = ItineraryDay.objects.create(trip=self.trip, date=date(2026, 1, 1), day_number=1)

        owner_login = self.client.post(
            reverse("accounts:login"), {"email": "owner@example.com", "password": "pass1234"}
        )
        self.owner_token = owner_login.data["tokens"]["access"]
        stranger_login = self.client.post(
            reverse("accounts:login"), {"email": "stranger@example.com", "password": "pass1234"}
        )
        self.stranger_token = stranger_login.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_owner_can_view_itinerary(self):
        response = self.client.get(
            reverse("itinerary:trip-itinerary", kwargs={"trip_pk": self.trip.pk}),
            **self._auth(self.owner_token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["days"]), 1)

    def test_stranger_gets_404_not_403(self):
        response = self.client.get(
            reverse("itinerary:trip-itinerary", kwargs={"trip_pk": self.trip.pk}),
            **self._auth(self.stranger_token),
        )
        # Deliberate difference from Chapter 7's TripDetailView (403) — see
        # Chapter 8 §10.5 rationale.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_item_to_day(self):
        response = self.client.post(
            reverse("itinerary:add-item", kwargs={"trip_pk": self.trip.pk, "day_pk": self.day.pk}),
            {"title": "Visit the museum", "start_time": "10:00"},
            **self._auth(self.owner_token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["order"], 10)
        self.assertFalse(response.data["is_ai_generated"])

    def test_cannot_add_item_to_day_of_others_trip(self):
        response = self.client.post(
            reverse("itinerary:add-item", kwargs={"trip_pk": self.trip.pk, "day_pk": self.day.pk}),
            {"title": "Sneaky item"},
            **self._auth(self.stranger_token),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.itinerary -v 2
```

---

## 15. Git Commit

```bash
git add apps/itinerary/ config/urls.py
git commit -m "feat(itinerary): ItineraryDay/ItineraryItem with N+1-safe reads

- Two-level parent-child: Trip -> ItineraryDay -> ItineraryItem, both
  CASCADE (meaningless independent of parent, per Architecture
  Handbook §5.8 reasoning); ItineraryItem.destination is SET_NULL
- day_number denormalized on ItineraryDay (documented trade-off,
  same class as Trip.computed_budget_total / ADR-7)
- is_ai_generated flag added now (defaults False) to avoid a
  disruptive migration once Chapter 12's agent starts writing here
- Gap-based ordering scheme (10, 20, 30...) in new services.py:
  add_item_to_day, insert_item_between, renumber_day (bulk_update,
  not per-row saves)
- New selectors.py pattern introduced: get_trip_itinerary() proven
  to run in a FIXED 2 queries regardless of trip size, via Prefetch
  + select_related nested two levels deep — verified directly with
  assertNumQueries, not just claimed
- TripItineraryView deliberately returns 404 (not 403) for another
  user's trip — documented deviation from Chapter 7's TripDetailView
- order field never client-writable; AddItineraryItemSerializer
  omits it entirely

Chapter 8 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `ItineraryDay`/`ItineraryItem` cascade correctly from `Trip`
- [ ] `ItineraryItem.destination` is `SET_NULL`, confirmed distinct from the CASCADE relations above it
- [ ] `unique_day_number_per_trip` and `unique_date_per_trip` constraints verified by tests
- [ ] `services.add_item_to_day`/`insert_item_between`/`renumber_day` all covered by isolated unit tests
- [ ] `selectors.get_trip_itinerary()` proven to use a **fixed** query count via `assertNumQueries`, tested against a deliberately large (14-day) trip
- [ ] `order` field is never accepted from client input anywhere in the write path
- [ ] Cross-user access to another user's itinerary returns 404 (documented as intentionally different from Chapter 7's 403)
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 9 — `budget` App: Cost Planning** builds `Budget` (one-to-one with `Trip`, mirroring Chapter 5's `Profile`/`User` pattern) and `BudgetLineItem` (many-to-one, mirroring this chapter's `ItineraryItem` pattern) — and is where `Trip.computed_budget_total` finally gets written to, via a signal that recalculates it every time a line item changes. This is the first chapter to combine a signal (Chapter 5's pattern) with aggregation queries (`Sum`), and the first place the "deliberate denormalization" trade-off documented back in Chapter 7 gets fully paid off. Say **"Continue to Chapter 9"** when ready.
