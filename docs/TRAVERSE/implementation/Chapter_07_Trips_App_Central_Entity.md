# Chapter 7 — `trips` App: The Central Entity

**Volume 2: Identity & Core Domain | Chapter 7 of 29**

> `Trip` is the object everything else in this project attaches to. Itinerary, budget, recommendations, AI agent runs, chat sessions — all of them, starting in Chapter 8, point back to a `Trip`. This chapter is where user-owned data (a `user` foreign key, like `Profile`) and reference data (a many-to-many to `Destination`) meet for the first time, where Chapter 3's `IsOwner` permission finally gets used for real, and where the project's first `services.py` file draws a firm line between "business logic" and "view logic."

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Model a many-to-many relationship correctly, including choosing between a plain M2M and a `through` model, and explain why we choose plain for now.
- Apply object-level permissions (`IsOwner`) on a real ID-based endpoint, and explain the difference from Chapter 5's ID-less profile endpoint.
- Separate "business rules" (`services.py`) from "HTTP plumbing" (`views.py`), and know exactly which of Chapter 3's `ApplicationError` subclasses to raise where.
- Enforce a date-range business rule (`end_date >= start_date`) at both the serializer and the database level, and explain why both layers matter.

---

## 2. Theory

### 2.1 Why `Trip` Needs Both a `user` FK AND a `destinations` M2M (ELI10)

A trip belongs to exactly one person (or, later, a group — see Architecture Handbook §13's `TripCollaborator`), so `user` is a straightforward one-to-many foreign key, same shape as `Profile`. But a single trip can span multiple cities (a two-week Japan trip touching Tokyo, Kyoto, and Osaka), and a single city can appear in many different people's trips — that's the textbook definition of many-to-many from Architecture Handbook §5.4.

### 2.2 Why `services.py` Exists Now, Not Before

Chapters 4-6 had views simple enough that putting logic directly in the view (or the serializer) was reasonable — a login check, a signal, a search filter. `Trip` introduces the first *real business rule* that isn't just field validation: "a trip's status can only move forward through a defined lifecycle" (draft → planning → planned → completed), and "creating a trip should default its status and immediately be tied to the requesting user, never a user ID from the request body." Once logic like this exists, cramming it into the view makes the view hard to read and hard to unit-test without spinning up an HTTP request. `services.py` holds this logic as plain, directly-testable Python functions; views become thin — they parse the request, call a service function, and format the response.

### 2.3 The Difference Between `IsOwner` Here and Chapter 5's Profile Endpoint

Chapter 5 sidestepped ownership checks entirely by never exposing an ID in the URL — `me/` was always the caller's own profile. `Trip` *must* expose an ID (`/trips/{id}/`), because a user has many trips, not one. This is exactly the scenario Chapter 3's `IsOwner` was built for: DRF's object-level permission system calls `has_object_permission(request, view, obj)` automatically for retrieve/update/delete actions, and we wire it in for the first time here.

---

## 3. Architecture Decision

**Decision:** `Trip.destinations` is a plain `ManyToManyField`, not a `through` model with extra fields, at this stage.

**Alternative considered:** Use a `through` model (`TripDestination`) from the start, anticipating future fields like "order visited" or "arrival date per destination." **Rejected for now because:** Chapter 8's `itinerary` app already owns day-by-day ordering and per-day destination association at a finer grain than trip-level — adding ordering data to the `Trip↔Destination` M2M itself would duplicate what `ItineraryDay`/`ItineraryItem` are about to do better. Documented as a YAGNI call in Section 15, explicitly reversible if a future need proves otherwise.

**Decision:** `Trip` uses Chapter 3's `UUIDPrimaryKeyModel`, unlike `Destination`'s plain integer PK.

**Why:** `Trip` IDs appear in personal, potentially-shared URLs (`/trips/{id}/`, and later Chapter 21's shareable document links). Sequential integer IDs would let a malicious actor enumerate `/trips/1/`, `/trips/2/`, ... and probe for other people's trips (even if `IsOwner` blocks the actual read, the *existence pattern* and volume of trips in the system would leak). UUIDs close that off, matching the exact reasoning `UUIDPrimaryKeyModel`'s own docstring gives in Chapter 3.

**Decision:** `Trip.status` is a `TextChoices` state machine enforced in the service layer, not just a free-editable field.

**Trade-off documented:** this adds a small amount of service-layer complexity (a transition-validation function) in exchange for guaranteeing the database can never contain a nonsensical status jump (e.g., `completed` → `draft`) via a direct API call — enterprise systems should not trust "the frontend will only send valid transitions."

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Trip` model | Needs `User` (Ch.4) and `Destination` (Ch.6) to already exist |
| Add DB-level `CheckConstraint` for date ordering | Must exist before any service-layer validation is trusted to be the *only* line of defense |
| Write `services.py` (create/update/status transition) | Needed before views, since views will call into it, not duplicate its logic |
| Write serializers | Needs to know exactly what the service layer expects/returns first |
| Write views using `IsOwner` | Last — everything it needs (service functions, serializers, permission class) already exists |

---

## 5. File Structure

```
apps/trips/
├── __init__.py
├── apps.py
├── models.py
├── services.py             # NEW pattern — business logic, no HTTP/DRF imports at all
├── serializers.py
├── permissions.py            # trip-specific permission composition (thin wrapper using core.IsOwner)
├── views.py
├── urls.py
├── admin.py
├── exceptions.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

**Why `services.py` has "no HTTP/DRF imports at all" as a hard rule:** this is what makes it unit-testable without `APITestCase`, without a request/response cycle, without authentication headers — just plain Python function calls with plain Python objects in, plain Python objects (or raised exceptions) out. Section 14 demonstrates this directly.

---

## 6. Folder Location

All new files under `apps/trips/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations trips
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.trips
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations trips
Migrations for 'trips':
  apps/trips/migrations/0001_initial.py
    - Create model Trip
    - Add field destinations to trip

$ curl -X POST http://localhost:8000/api/v1/trips/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Japan Adventure", "start_date": "2026-10-01", "end_date": "2026-10-14", "destination_ids": [1, 2]}'

{"id": "b3f1...", "title": "Japan Adventure", "status": "draft", ...}
```

---

## 10. Code

### 10.1 `apps/trips/models.py`

```python
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class TripStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PLANNING = "planning", "AI Planning In Progress"
    PLANNED = "planned", "Planned"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Trip(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    The central entity of the entire project. Everything from
    Chapter 8 onward (itinerary, budget, recommendations, agent
    runs, chat sessions, documents) points back to a Trip.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips",
    )
    destinations = models.ManyToManyField(
        "destinations.Destination",
        related_name="trips",
        blank=True,
    )
    title = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=TripStatus.choices, default=TripStatus.DRAFT, db_index=True,
    )
    traveler_count = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)

    # Deliberate denormalization, per Architecture Handbook ADR-7 —
    # refreshed by a signal in budget's app (Chapter 9), never
    # written to directly outside that one path.
    computed_budget_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, editable=False,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gte=models.F("start_date")),
                name="trip_end_date_gte_start_date",
            ),
        ]
        verbose_name = "Trip"
        verbose_name_plural = "Trips"

    def __str__(self) -> str:
        return f"{self.title} ({self.user.email})"

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1
```

**Why `computed_budget_total` is `editable=False`**: this is the enforcement mechanism behind Architecture Handbook ADR-7's promise that this field is "never written to directly outside that one [signal] path" — `editable=False` excludes it from `ModelForm`/admin form auto-generation, and it is deliberately left out of `TripSerializer.fields` in Section 10.5 so the API can't accidentally accept it either. Both mechanisms are documented here so they don't drift apart silently in a future edit.

**Why `models.Index(fields=["user", "status"])` and not two separate single-field indexes:** this exactly matches Architecture Handbook §5.6's stated dashboard query pattern — "my active trips" filters on both fields together, and a composite index serves that combined filter far more efficiently than two independent indexes would.

### 10.2 `apps/trips/exceptions.py`

```python
from apps.core.exceptions import ApplicationError, BusinessRuleViolation


class InvalidStatusTransition(BusinessRuleViolation):
    default_message = "This status change is not allowed from the trip's current status."
    default_code = "invalid_status_transition"


class InvalidDateRange(BusinessRuleViolation):
    default_message = "Trip end date must be on or after the start date."
    default_code = "invalid_date_range"
```

### 10.3 `apps/trips/services.py`

```python
"""
Business logic for the trips app.

RULE: this module never imports anything from rest_framework or
django.http. It takes plain Python/Django ORM objects in, returns
plain Django model instances or raises ApplicationError subclasses.
This is what makes every function here directly unit-testable
without an HTTP client (see tests/test_services.py).
"""
from datetime import date

from apps.trips.exceptions import InvalidDateRange, InvalidStatusTransition
from apps.trips.models import Trip, TripStatus

# Defines which status transitions are legal. A status can only move
# to one of the values in its own set below — anything else is rejected.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    TripStatus.DRAFT: {TripStatus.PLANNING, TripStatus.CANCELLED},
    TripStatus.PLANNING: {TripStatus.PLANNED, TripStatus.DRAFT, TripStatus.CANCELLED},
    TripStatus.PLANNED: {TripStatus.COMPLETED, TripStatus.CANCELLED},
    TripStatus.COMPLETED: set(),   # terminal state — no transitions out
    TripStatus.CANCELLED: set(),   # terminal state — no transitions out
}


def validate_date_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise InvalidDateRange()


def create_trip(*, user, title: str, start_date: date, end_date: date,
                 destination_ids: list[int] | None = None,
                 traveler_count: int = 1, notes: str = "") -> Trip:
    validate_date_range(start_date, end_date)

    trip = Trip.objects.create(
        user=user,
        title=title,
        start_date=start_date,
        end_date=end_date,
        traveler_count=traveler_count,
        notes=notes,
        status=TripStatus.DRAFT,
    )
    if destination_ids:
        trip.destinations.set(destination_ids)
    return trip


def update_trip_dates(*, trip: Trip, start_date: date, end_date: date) -> Trip:
    validate_date_range(start_date, end_date)
    trip.start_date = start_date
    trip.end_date = end_date
    trip.save(update_fields=["start_date", "end_date", "updated_at"])
    return trip


def transition_trip_status(*, trip: Trip, new_status: str) -> Trip:
    allowed = _ALLOWED_TRANSITIONS.get(trip.status, set())
    if new_status not in allowed:
        raise InvalidStatusTransition(
            message=f"Cannot move trip from '{trip.status}' to '{new_status}'."
        )
    trip.status = new_status
    trip.save(update_fields=["status", "updated_at"])
    return trip
```

**Why `_ALLOWED_TRANSITIONS` is a module-level dict, not scattered `if` statements**: this makes the entire state machine visible and reviewable in one place — anyone can look at this dict and know every legal transition without reading through branching logic. It's also directly testable in isolation (Section 14 tests it exhaustively).

**Why `create_trip` takes `user` as a keyword-only parameter, never reading it from anywhere else**: this is a deliberate security-relevant design choice — the trip's owner is *always* whoever the view passes in (which will always be `request.user`, never a client-supplied `user_id` field). This structurally prevents a "create a trip on someone else's behalf" vulnerability, the same category of protection Chapter 5's ID-less profile endpoint provides, applied here at the service-function-signature level instead.

### 10.4 `apps/trips/permissions.py`

```python
"""
Trip-specific permission composition. Thin — the real ownership
logic lives in apps.core.permissions.IsOwner (Chapter 3). This file
exists so trip views import from `trips.permissions`, keeping each
app's import surface self-contained even when it's just a re-export.
"""
from apps.core.permissions import IsOwner

__all__ = ["IsOwner"]
```

### 10.5 `apps/trips/serializers.py`

```python
from rest_framework import serializers

from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationSerializer
from apps.trips.models import Trip


class TripSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=True)
    destination_ids = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.filter(is_active=True),
        many=True, write_only=True, required=False, source="destinations",
    )
    duration_days = serializers.ReadOnlyField()

    class Meta:
        model = Trip
        fields = [
            "id", "title", "start_date", "end_date", "status",
            "traveler_count", "notes", "destinations", "destination_ids",
            "duration_days", "computed_budget_total", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "computed_budget_total", "created_at", "updated_at"]

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "must be on or after start_date."}
            )
        return attrs


class TripStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Trip._meta.get_field("status").choices)
```

**Why both `destinations` (read, nested, full detail) and `destination_ids` (write, PK list) exist as separate fields mapped to the same underlying relation via `source="destinations"`**: this is a standard, deliberate DRF pattern — API clients read rich destination objects (name, country, cost estimate) but write using simple ID lists, which is both a smaller payload and avoids ambiguity about whether a write should create/update a `Destination` versus merely *link* to an existing one (it should only ever link — see `status` field also being read-only here for a related reason: transitions must go through `TripStatusUpdateSerializer` + the service layer's validated state machine, never a raw `PATCH` on `status` directly).

**Why `status` is `read_only_fields` on `TripSerializer` but has its own separate `TripStatusUpdateSerializer`**: this forces every status change through the dedicated endpoint (Section 10.6) that calls `transition_trip_status()`, rather than allowing a generic `PATCH /trips/{id}/` with `{"status": "completed"}` to silently bypass the state machine validated in `services.py`.

### 10.6 `apps/trips/views.py`

```python
from rest_framework import status as http_status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trips import services
from apps.trips.models import Trip
from apps.trips.permissions import IsOwner
from apps.trips.serializers import TripSerializer, TripStatusUpdateSerializer


class TripListCreateView(ListCreateAPIView):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Trip.objects.filter(user=self.request.user).prefetch_related("destinations")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination_objs = serializer.validated_data.pop("destinations", [])
        trip = services.create_trip(
            user=request.user,
            destination_ids=[d.id for d in destination_objs],
            **serializer.validated_data,
        )
        return Response(TripSerializer(trip).data, status=http_status.HTTP_201_CREATED)


class TripDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = Trip.objects.all().prefetch_related("destinations")

    def perform_update(self, serializer):
        if "start_date" in serializer.validated_data or "end_date" in serializer.validated_data:
            trip = self.get_object()
            services.update_trip_dates(
                trip=trip,
                start_date=serializer.validated_data.get("start_date", trip.start_date),
                end_date=serializer.validated_data.get("end_date", trip.end_date),
            )
        serializer.save()


class TripStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]

    def get_object(self, pk):
        from django.shortcuts import get_object_or_404
        trip = get_object_or_404(Trip, pk=pk)
        self.check_object_permissions(self.request, trip)
        return trip

    def post(self, request, pk):
        trip = self.get_object(pk)
        serializer = TripStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = services.transition_trip_status(
            trip=trip, new_status=serializer.validated_data["status"]
        )
        return Response(TripSerializer(updated).data)
```

**Why `TripListCreateView.get_queryset()` always filters by `user=self.request.user`, with no dependency on `IsOwner` at all for the list view**: `IsOwner` is an *object-level* permission — it only ever runs on retrieve/update/delete of a single, already-fetched object. A list endpoint has no single object to check, so ownership has to be enforced at the queryset level instead. This is a common point of confusion worth stating explicitly: **list views need queryset-level scoping; detail views need `IsOwner`; both are required, neither substitutes for the other.**

**Why `TripDetailView.queryset = Trip.objects.all()` (not filtered to the current user) despite `IsOwner` being applied**: DRF's generic views need `get_object()` to be able to *find* the trip first (returning 404 if it truly doesn't exist for anyone), and only *then* does `IsOwner.has_object_permission` decide if this particular requester may access it (returning 403 if it exists but isn't theirs, exactly matching Chapter 3's documented reasoning for why `ResourceNotOwned` maps to 403, not 404).

### 10.7 `apps/trips/urls.py`

```python
from django.urls import path

from apps.trips.views import TripDetailView, TripListCreateView, TripStatusUpdateView

app_name = "trips"

urlpatterns = [
    path("", TripListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", TripDetailView.as_view(), name="detail"),
    path("<uuid:pk>/status/", TripStatusUpdateView.as_view(), name="status-update"),
]
```

### 10.8 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.trips.urls")),
```

### 10.9 `apps/trips/admin.py`

```python
from django.contrib import admin

from apps.trips.models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "status", "start_date", "end_date", "created_at"]
    list_filter = ["status", "start_date"]
    search_fields = ["title", "user__email"]
    autocomplete_fields = ["user", "destinations"]
    readonly_fields = ["created_at", "updated_at", "computed_budget_total"]
```

---

## 11. Code Walkthrough

- **`create_trip()` pops `destination_ids` and sets them via `.set()` after the trip is already saved, not in the same `objects.create()` call**: M2M relationships require the object to already have a primary key before any related rows can be linked — this is a Django ORM constraint, not a stylistic choice, and is a very common beginner stumbling block worth calling out directly.
- **The view's `create()` is overridden instead of relying on `perform_create()`**: the default `ListCreateAPIView.create()`/`perform_create()` flow assumes the serializer's `.save()` does everything. Here, we need to route through `services.create_trip()` instead of `serializer.save()`, so the view's `create()` method is fully overridden — this is a deliberate, documented deviation from the "usual" DRF generic view flow, chosen specifically so the business rule validation (date range) and the ownership assignment both flow through the one tested `services.py` function rather than being duplicated in the serializer.
- **`_ALLOWED_TRANSITIONS[TripStatus.COMPLETED] = set()`**: an empty set as the allowed-transitions value for a terminal state is the cleanest possible way to express "nothing can happen after this" — no special-casing needed anywhere else in the transition-checking logic.
- **`CheckConstraint` (DB-level) AND `validate_date_range()`/serializer `validate()` (app-level) both enforce the same rule**: this is intentional defense in depth, not redundancy for its own sake — the DB constraint is the last line of defense against *any* code path (a future data migration, a bulk import script, a bug that bypasses `services.py`) that might otherwise insert a bad row; the app-level checks exist purely to give a friendly, immediate error message instead of a raw database exception.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `django.db.utils.IntegrityError: new row for relation "trips_trip" violates check constraint "trip_end_date_gte_start_date"` | Some code path bypassed `services.validate_date_range()` entirely | This is the DB-level safety net working as intended — trace back which code path skipped the service layer and route it through `services.py` instead |
| `403 Forbidden` on `/trips/{id}/` for a trip you're sure is yours | Testing with a stale/wrong access token from a different user | Re-login, confirm the `Authorization` header's token actually belongs to the trip's owner |
| `TypeError: create_trip() missing 1 required keyword-only argument: 'user'` | Called `services.create_trip()` positionally instead of with keywords | All `services.py` functions use keyword-only arguments (the bare `*`) deliberately, to prevent accidental positional-argument mix-ups (e.g., swapping `start_date`/`end_date`) — always call with explicit keywords |
| Status stuck, `POST /trips/{id}/status/` always returns `invalid_status_transition` | Trying to skip a state (e.g., `draft` → `completed` directly) | Check `_ALLOWED_TRANSITIONS` — this is correct, intentional behavior, not a bug |

---

## 13. Debugging

```bash
# 1. Test the state machine directly in the shell, no HTTP needed
docker compose exec web python manage.py shell -c "
from apps.trips import services
from apps.trips.models import Trip, TripStatus
from django.contrib.auth import get_user_model
user = get_user_model().objects.first()
trip = services.create_trip(user=user, title='Test', start_date='2026-01-01', end_date='2026-01-05')
print(trip.status)
trip = services.transition_trip_status(trip=trip, new_status=TripStatus.PLANNING)
print(trip.status)
"

# 2. Confirm the composite index is actually used by the dashboard query
docker compose exec web python manage.py shell -c "
from django.db import connection
from apps.trips.models import Trip
list(Trip.objects.filter(user_id=1, status='draft'))
print(connection.queries[-1]['sql'])
"
```

**Rollback strategy:** if a bad `Trip` row somehow makes it past both layers of date validation (should be structurally impossible, but worth having a plan), fix it via a one-off `python manage.py shell` correction, then add a regression test in `test_services.py` reproducing the exact input that caused it, per Architecture Handbook §14's "regression tests stay fixed" principle.

---

## 14. Testing

### 14.1 `apps/trips/tests/test_services.py` (the payoff of the "no DRF imports" rule)

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.trips import services
from apps.trips.exceptions import InvalidDateRange, InvalidStatusTransition
from apps.trips.models import TripStatus

User = get_user_model()


class CreateTripServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="t@example.com", password="pass1234")

    def test_create_trip_defaults_to_draft(self):
        trip = services.create_trip(
            user=self.user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )
        self.assertEqual(trip.status, TripStatus.DRAFT)
        self.assertEqual(trip.user, self.user)

    def test_create_trip_with_invalid_dates_raises(self):
        with self.assertRaises(InvalidDateRange):
            services.create_trip(
                user=self.user, title="Bad", start_date=date(2026, 1, 5), end_date=date(2026, 1, 1)
            )

    def test_create_trip_links_destinations(self):
        d1 = Destination.objects.create(name="Tokyo", country="Japan")
        d2 = Destination.objects.create(name="Kyoto", country="Japan")
        trip = services.create_trip(
            user=self.user, title="Japan", start_date=date(2026, 1, 1), end_date=date(2026, 1, 10),
            destination_ids=[d1.id, d2.id],
        )
        self.assertEqual(trip.destinations.count(), 2)


class TransitionTripStatusServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="t2@example.com", password="pass1234")
        self.trip = services.create_trip(
            user=self.user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )

    def test_draft_to_planning_allowed(self):
        updated = services.transition_trip_status(trip=self.trip, new_status=TripStatus.PLANNING)
        self.assertEqual(updated.status, TripStatus.PLANNING)

    def test_draft_to_completed_directly_rejected(self):
        with self.assertRaises(InvalidStatusTransition):
            services.transition_trip_status(trip=self.trip, new_status=TripStatus.COMPLETED)

    def test_completed_is_terminal(self):
        self.trip.status = TripStatus.COMPLETED
        self.trip.save()
        with self.assertRaises(InvalidStatusTransition):
            services.transition_trip_status(trip=self.trip, new_status=TripStatus.PLANNING)

    def test_full_happy_path_lifecycle(self):
        trip = self.trip
        for target in [TripStatus.PLANNING, TripStatus.PLANNED, TripStatus.COMPLETED]:
            trip = services.transition_trip_status(trip=trip, new_status=target)
            self.assertEqual(trip.status, target)
```

### 14.2 `apps/trips/tests/test_views.py`

```python
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.trips.models import Trip

User = get_user_model()


class TripAPITests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email="a@example.com", password="pass1234")
        self.user_b = User.objects.create_user(email="b@example.com", password="pass1234")
        self.token_a = self._login("a@example.com")
        self.token_b = self._login("b@example.com")

    def _login(self, email):
        response = self.client.post(
            reverse("accounts:login"), {"email": email, "password": "pass1234"}
        )
        return response.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_create_trip(self):
        response = self.client.post(
            reverse("trips:list-create"),
            {"title": "My Trip", "start_date": "2026-06-01", "end_date": "2026-06-10"},
            **self._auth(self.token_a),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "draft")

    def test_create_trip_bad_dates_returns_400(self):
        response = self.client.post(
            reverse("trips:list-create"),
            {"title": "Bad", "start_date": "2026-06-10", "end_date": "2026-06-01"},
            **self._auth(self.token_a),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_only_sees_own_trips_in_list(self):
        self.client.post(
            reverse("trips:list-create"),
            {"title": "A's trip", "start_date": "2026-06-01", "end_date": "2026-06-10"},
            **self._auth(self.token_a),
        )
        self.client.post(
            reverse("trips:list-create"),
            {"title": "B's trip", "start_date": "2026-07-01", "end_date": "2026-07-10"},
            **self._auth(self.token_b),
        )
        response = self.client.get(reverse("trips:list-create"), **self._auth(self.token_a))
        titles = [t["title"] for t in response.data["results"]]
        self.assertEqual(titles, ["A's trip"])

    def test_user_cannot_retrieve_others_trip(self):
        create_response = self.client.post(
            reverse("trips:list-create"),
            {"title": "A's trip", "start_date": "2026-06-01", "end_date": "2026-06-10"},
            **self._auth(self.token_a),
        )
        trip_id = create_response.data["id"]
        response = self.client.get(
            reverse("trips:detail", kwargs={"pk": trip_id}), **self._auth(self.token_b)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_transition_endpoint(self):
        create_response = self.client.post(
            reverse("trips:list-create"),
            {"title": "A's trip", "start_date": "2026-06-01", "end_date": "2026-06-10"},
            **self._auth(self.token_a),
        )
        trip_id = create_response.data["id"]
        response = self.client.post(
            reverse("trips:status-update", kwargs={"pk": trip_id}),
            {"status": "planning"},
            **self._auth(self.token_a),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "planning")

    def test_direct_patch_of_status_field_is_ignored_not_erroring(self):
        create_response = self.client.post(
            reverse("trips:list-create"),
            {"title": "A's trip", "start_date": "2026-06-01", "end_date": "2026-06-10"},
            **self._auth(self.token_a),
        )
        trip_id = create_response.data["id"]
        response = self.client.patch(
            reverse("trips:detail", kwargs={"pk": trip_id}),
            {"status": "completed"},
            **self._auth(self.token_a),
        )
        # status is read_only on TripSerializer — must remain "draft"
        trip = Trip.objects.get(pk=trip_id)
        self.assertEqual(trip.status, "draft")
```

Run everything:

```bash
docker compose exec web python manage.py test apps.trips -v 2
```

---

## 15. Git Commit

```bash
git add apps/trips/ config/urls.py
git commit -m "feat(trips): central Trip entity, state machine, ownership enforcement

- Trip: UUID PK (Chapter 3's UUIDPrimaryKeyModel — enumeration
  protection for personal, potentially-shared URLs), user FK
  (CASCADE), destinations M2M to Destination (plain M2M for now,
  through-model deferred as YAGNI — see Chapter 7 ADR)
- computed_budget_total: editable=False, excluded from serializer,
  written only by Chapter 9's signal (Architecture Handbook ADR-7)
- DB CheckConstraint + service-layer validate_date_range() — defense
  in depth on the start/end date business rule
- First services.py in the project: zero DRF imports, fully
  unit-testable status state machine (_ALLOWED_TRANSITIONS) and
  create_trip()/update_trip_dates()/transition_trip_status()
- IsOwner (Chapter 3) used for real for the first time on
  TripDetailView/TripStatusUpdateView; queryset-level user filtering
  on the list view (object-level permissions don't apply to lists)
- Status changes routed exclusively through /trips/{id}/status/,
  never via direct PATCH — status is read_only on TripSerializer
- Full coverage: service layer in isolation, cross-user ownership
  enforcement (403 not 404, per Chapter 3), state machine edge cases

Chapter 7 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Trip` uses `UUIDPrimaryKeyModel`, not an integer PK
- [ ] `destinations` M2M correctly links/unlinks via `.set()` in `services.create_trip()`
- [ ] `computed_budget_total` is `editable=False` and absent from `TripSerializer.fields`
- [ ] DB `CheckConstraint` on `end_date >= start_date` verified by a failing-transaction test
- [ ] `services.py` has zero `rest_framework`/`django.http` imports — confirmed by inspection
- [ ] `_ALLOWED_TRANSITIONS` covers every `TripStatus` value, including empty sets for terminal states
- [ ] `IsOwner` applied to `TripDetailView` and `TripStatusUpdateView`; cross-user access returns 403, not 404
- [ ] List view scoped to `request.user` at the queryset level (not relying on `IsOwner` alone)
- [ ] Direct `PATCH` of `status` is silently ignored (field is read-only), status only changes via the dedicated endpoint
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 8 — `itinerary` App: Day-by-Day Planning** builds `ItineraryDay` and `ItineraryItem`, the first two-level parent-child relationship in the project (a day belongs to a trip, an item belongs to a day), along with explicit item ordering logic — the exact fine-grained, per-day destination association that Chapter 7's ADR deferred out of the `Trip↔Destination` M2M. This is also where we first write a query with `prefetch_related` chained two levels deep, and reason carefully about N+1 query risk before it becomes a real performance problem. Say **"Continue to Chapter 8"** when ready.
