# Chapter 23 — `bookings` App (Placeholder)

**Volume 6: Supporting Apps | Chapter 23 of 29**

> This is the smallest chapter in the entire project, and that's the point. `bookings` reserves the shape Architecture Handbook §13's marketplace roadmap ("Hotel Booking," "Flight Comparison," "Travel Marketplace") will eventually need, without building any of the actual integration those features require. No payment processing, no partner APIs, no `ai/tools/` additions — just a model that captures a user's *intent* to book something, and the deliberate, documented restraint not to build further than that intent actually calls for right now.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Recognize when the right amount of engineering effort for a feature is genuinely small, and build exactly that — not a placeholder that secretly does more than it should, and not something so bare it provides no real value either.
- Design a model that captures user *intent* separately from a *transaction*, understanding why these are different things even when they'll eventually be connected.
- Read Architecture Handbook §13's future roadmap correctly: as a description of shape to reserve, not a checklist to rush toward implementing early.

---

## 2. Theory

### 2.1 Why This Chapter Exists At All, If It Builds "Nothing Real" (ELI10)

Imagine a house being built with a marked, framed-out doorway leading to a room that hasn't been built yet — the doorway itself is useful today (it stops someone from mistakenly building a wall where a door needs to go later), even though the room behind it doesn't exist yet. `bookings` is that doorway: a `Booking` model capturing "I want to book this" is genuinely useful *today* — as a wishlist, as a signal of user interest, as something a UI can show right now — without needing a single line of payment or partner-API code to already exist.

### 2.2 Why "Intent" and "Transaction" Are Different Concepts, Even Though They'll Connect Later

A user clicking "I'd like to book this hotel" is expressing a preference — genuinely useful data on its own (a signal for future recommendations, a thing they can review later, potentially something Chapter 24's analytics could aggregate). Actually *booking* a hotel — charging a card, reserving a room with a real partner, handling cancellation policies — is an entirely different, much larger problem, involving real money, real external contracts, and real failure modes this project has no infrastructure for yet. Building the "intent" concept now, cleanly separated from any assumption about how "transaction" will eventually work, means this chapter's small piece of work won't need to be torn up when real booking integration eventually arrives — it'll simply gain a new relationship pointing at it.

---

## 3. Architecture Decision

**Decision:** `Booking` has exactly one meaningful status for now — `INTENT_ONLY` — with `CONFIRMED`/`CANCELLED` reserved in the `TextChoices` enum but never actually reachable through any code path yet.

**Alternative considered:** Build a full booking status state machine now (matching Chapter 7's `Trip` or Chapter 10's `Recommendation` transition-table pattern), anticipating the states a real booking would eventually need. **Rejected because:** a state machine for `CONFIRMED`/`CANCELLED` implies transitions triggered by *real events* (a partner API confirming a reservation, a user cancelling a real booking) that don't exist yet — building the transition logic now would be guessing at a shape informed by an integration this project hasn't designed, exactly the premature-abstraction trap this chapter is explicitly built to avoid.

**Decision:** `Booking.source_recommendation` is an optional foreign key back to Chapter 10's `Recommendation`, letting a booking intent originate from an AI suggestion the user liked enough to act on.

**Why this one connection is worth building now, while everything else stays minimal:** it's cheap (one nullable FK) and it closes a real, already-existing loop — Chapter 15's Recommendation Agent already produces suggestions; letting a user turn "I like this suggestion" into "I want to book this" is a natural, small extension of data that already exists, not new speculative infrastructure.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Booking` model + migration | Needed before anything else |
| Write the one service function (`create_booking_intent`) | Needed before the view |
| Build the minimal list/create API | Last — there is genuinely nothing else to build yet |

---

## 5. File Structure

```
apps/bookings/
├── __init__.py
├── apps.py
├── models.py                    # Booking
├── services.py                   # create_booking_intent — the ONE function
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_views.py
```

**Notice what's absent, deliberately**: no `selectors.py` (no query complex enough to need one yet), no `tasks.py` (nothing async happens here), no `exceptions.py` (no business rule complex enough to need a dedicated exception yet). An empty file created "just in case" would misrepresent how much is actually here — the file list itself is honest about the chapter's real scope.

---

## 6. Folder Location

New files under `apps/bookings/` (already scaffolded empty since Chapter 2).

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations bookings
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.bookings -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ curl -X POST http://localhost:8000/api/v1/trips/<trip_id>/bookings/ \
  -H "Authorization: Bearer <access>" \
  -d '{"booking_type": "hotel", "title": "Riverside Boutique Hotel", "estimated_cost": "450.00"}'
{"id": "e5f2...", "booking_type": "hotel", "title": "Riverside Boutique Hotel", "status": "intent_only", "estimated_cost": "450.00"}
```

---

## 10. Code

### 10.1 `apps/bookings/models.py`

```python
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class BookingType(models.TextChoices):
    FLIGHT = "flight", "Flight"
    HOTEL = "hotel", "Hotel"
    ACTIVITY = "activity", "Activity"
    OTHER = "other", "Other"


class BookingStatus(models.TextChoices):
    INTENT_ONLY = "intent_only", "Intent Only"
    # Reserved for real integration, NOT reachable by any code path
    # yet — see Chapter 23 Architecture Decision for why building
    # their transitions now would be premature.
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class Booking(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Captures a user's INTENT to book something — not a real
    transaction. See Chapter 23 Theory §2.2 for why these are kept
    conceptually and structurally separate.
    """
    trip = models.ForeignKey("trips.Trip", on_delete=models.CASCADE, related_name="bookings")
    source_recommendation = models.ForeignKey(
        "recommendations.Recommendation", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="bookings",
        help_text="Optional. If this booking intent originated from an AI "
                   "recommendation the user acted on.",
    )
    booking_type = models.CharField(max_length=20, choices=BookingType.choices)
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.INTENT_ONLY)
    title = models.CharField(max_length=200)
    estimated_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking Intent"
        verbose_name_plural = "Booking Intents"

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"
```

**Why `source_recommendation` uses `SET_NULL`, matching `ItineraryItem.destination`'s (Chapter 8) reasoning exactly**: a booking intent's *own* record (the user's expressed interest) has value independent of whether the recommendation that inspired it still exists — deleting the source recommendation shouldn't destroy the booking intent it led to.

### 10.2 `apps/bookings/services.py`

```python
"""
One function. That's the whole file — see Chapter 23 for why
building more here right now would be premature.
"""
from apps.bookings.models import Booking


def create_booking_intent(
    *, trip, booking_type: str, title: str, estimated_cost=None,
    notes: str = "", source_recommendation=None,
) -> Booking:
    return Booking.objects.create(
        trip=trip, booking_type=booking_type, title=title,
        estimated_cost=estimated_cost, notes=notes, source_recommendation=source_recommendation,
    )
```

### 10.3 `apps/bookings/serializers.py`

```python
from rest_framework import serializers

from apps.bookings.models import Booking


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "booking_type", "status", "title", "estimated_cost",
            "notes", "source_recommendation", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
```

### 10.4 `apps/bookings/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.trips.models import Trip


class TripBookingListCreateView(ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        trip = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], user=self.request.user)
        return Booking.objects.filter(trip=trip)

    def perform_create(self, serializer):
        trip = get_object_or_404(Trip, pk=self.kwargs["trip_pk"], user=self.request.user)
        serializer.save(trip=trip)
```

**Why this view uses `perform_create` (a standard DRF generic-view hook) rather than the fully custom `create()` override every other creation endpoint in this project has used (Chapter 7's `TripListCreateView`, for instance)**: those custom overrides existed specifically to route through a `services.py` function carrying real business logic (date validation, status defaults, M2M linking). This view's "business logic" is genuinely just "create the row with the given trip" — `perform_create`'s minimal hook is the *correct*, right-sized amount of structure for a creation path this simple, not a shortcut avoiding a pattern the project otherwise always uses. Reaching for the heavier custom-`create()` pattern here, out of habit, would itself be a small instance of the over-building this chapter is about avoiding.

### 10.5 `apps/bookings/urls.py`

```python
from django.urls import path

from apps.bookings.views import TripBookingListCreateView

app_name = "bookings"

urlpatterns = [
    path("<uuid:trip_pk>/bookings/", TripBookingListCreateView.as_view(), name="list-create"),
]
```

### 10.6 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.bookings.urls")),
```

### 10.7 `apps/bookings/admin.py`

```python
from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["title", "trip", "booking_type", "status", "estimated_cost"]
    list_filter = ["booking_type", "status"]
    search_fields = ["title", "trip__title"]
```

---

## 11. Code Walkthrough

- **The entire chapter's business logic fits in one four-line function**: this is worth sitting with, not glossing past — after 22 chapters of increasingly sophisticated services, selectors, signals, and multi-agent orchestration, recognizing that *this particular problem*, at *this particular stage of the project*, genuinely needs almost none of that machinery is itself a skill. The temptation to add a `selectors.py` "for consistency" or a status transition table "to match the pattern" is exactly the instinct worth resisting here.
- **`BookingStatus.CONFIRMED`/`CANCELLED` exist in the enum but are unreachable by design** — a small, deliberate echo of Chapter 12's `AgentType.TRAVEL_PLANNER`/`FULL_GRAPH` reserved-but-unused-yet values, and Chapter 3's empty `tools/`/`memory/`/`agents/`/`graphs/` folders: reserving a name in the vocabulary costs nothing and avoids a future naming collision, without requiring the behavior behind it to exist yet.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| Expecting a `status` transition endpoint (like Chapter 7's `/trips/{id}/status/`) that doesn't exist | Assuming every model with a `status` field gets the same transition-endpoint treatment | Not yet — `status` only has one real value right now; a transition endpoint has nothing meaningful to transition between yet |
| Trying to set `status` to `confirmed` directly via the API | `status` is `read_only` on `BookingSerializer` | Expected — there's no real confirmation flow yet for it to represent |
| Looking for a `services.py` function to update/cancel a booking | Doesn't exist yet, deliberately | This is accurate — build it when real booking integration is added, not before |

---

## 13. Debugging

```bash
docker compose exec web python manage.py shell -c "
from apps.bookings import services
from apps.trips.models import Trip
trip = Trip.objects.first()
booking = services.create_booking_intent(trip=trip, booking_type='hotel', title='Test Hotel')
print(booking.status)
"
```

**Rollback strategy:** nothing to roll back — `Booking` rows have no relationships pointing *at* them from anywhere else in the system yet, so deleting a mistaken row is always trivially safe.

---

## 14. Testing

### 14.1 `apps/bookings/tests/test_models.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bookings.models import Booking, BookingStatus
from apps.trips.models import Trip

User = get_user_model()


class BookingModelTests(TestCase):
    def test_default_status_is_intent_only(self):
        user = User.objects.create_user(email="b@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        booking = Booking.objects.create(trip=trip, booking_type="hotel", title="Test Hotel")
        self.assertEqual(booking.status, BookingStatus.INTENT_ONLY)
```

### 14.2 `apps/bookings/tests/test_views.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.trips.models import Trip

User = get_user_model()


class BookingViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="v@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=self.user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))
        login = self.client.post(reverse("accounts:login"), {"email": "v@example.com", "password": "pass1234"})
        self.token = login.data["tokens"]["access"]

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_create_booking_intent(self):
        response = self.client.post(
            reverse("bookings:list-create", kwargs={"trip_pk": self.trip.pk}),
            {"booking_type": "hotel", "title": "Test Hotel", "estimated_cost": "200.00"},
            **self._auth(),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "intent_only")

    def test_status_cannot_be_set_directly(self):
        response = self.client.post(
            reverse("bookings:list-create", kwargs={"trip_pk": self.trip.pk}),
            {"booking_type": "hotel", "title": "Test", "status": "confirmed"},
            **self._auth(),
        )
        self.assertEqual(response.data["status"], "intent_only")
```

Run everything:

```bash
docker compose exec web python manage.py test apps.bookings -v 2
```

---

## 15. Git Commit

```bash
git add apps/bookings/ config/urls.py
git commit -m "feat(bookings): placeholder app — intent capture only, no integration

- Booking captures user INTENT, deliberately separate from any real
  transaction — no payment, no partner API, no ai/tools addition
- BookingStatus.CONFIRMED/CANCELLED reserved in the enum, unreachable
  by any code path yet — same 'reserve the name, not the behavior'
  pattern as Chapter 12's AgentType.FULL_GRAPH before Chapter 17
- source_recommendation (SET_NULL) closes one small, real loop: a
  Recommendation the user liked can become a booking intent — the
  one connection worth building now, everything else deferred
- Entire business logic: one 4-line service function; no selectors,
  no tasks, no exceptions — file list itself honestly reflects scope
- View uses perform_create() (standard DRF hook), not a custom
  create() override — right-sized for logic this simple, not a
  shortcut around the project's usual services.py pattern

Smallest chapter in the project, by design. Chapter 23 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Booking.status` only ever produces `intent_only` through any real code path
- [ ] `source_recommendation` uses `SET_NULL`, consistent with Chapter 8's reasoning for the same shape
- [ ] `status` is read-only on the serializer — confirmed a client cannot set it directly
- [ ] No `selectors.py`, `tasks.py`, or `exceptions.py` files exist — scope matches reality
- [ ] All tests passing
- [ ] Commit made
- [ ] **This chapter is genuinely done being small** — resist the urge to add more before Chapter 24

---

## 17. Next Chapter Preview

**Chapter 24 — `analytics` App** closes Volume 6. It's the read-only consumer of every other app built so far (Architecture Handbook §4.4: "never writes to other apps' tables directly, only reads"), aggregating usage data across trips, agent runs, and now — thanks to this chapter — booking intents, into admin-facing dashboards. This is also the first chapter to seriously think about query performance at the aggregate, cross-app level, rather than the single-trip scope every prior chapter's `assertNumQueries` tests have focused on. Say **"Continue to Chapter 24"** when ready.
