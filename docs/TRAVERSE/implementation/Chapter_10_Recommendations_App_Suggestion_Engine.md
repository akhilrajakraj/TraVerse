# Chapter 10 — `recommendations` App: Suggestion Engine (Data Layer)

**Volume 3: Trip Sub-Domains | Chapter 10 of 29**

> This chapter closes out Volume 3. `Recommendation` is read-mostly, AI-populated data — per Architecture Handbook §4.4, "read-mostly, AI-populated, user can accept/reject." Critically, **this chapter builds only the data layer and API**: the model, the accept/reject state machine, and endpoints. The actual intelligence that generates recommendations doesn't exist until Chapter 15's Recommendation Agent. This is the third time in the project we build "the container before the content" — the same discipline already applied to itinerary (Chapter 8) and budget (Chapter 9), and it's worth naming explicitly as a pattern before Volume 4 begins.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Recognize and name the "structure first, intelligence later" pattern this project has now used three times, and why it's a deliberate strategy rather than incidental sequencing.
- Model a suggestion/decision workflow (`pending` → `accepted`/`rejected`) as a small state machine, reusing the exact transition-table technique from Chapter 7's `Trip` status, applied to a simpler two-outcome case.
- Build a management command that seeds *fake* AI-style recommendations for development/testing, so Chapters 15 and 17 have real data to develop against before the actual agent exists.
- Understand why `Recommendation.score` exists now even though nothing computes a meaningful value for it until Chapter 15.

---

## 2. Theory

### 2.1 Why "Structure First, Intelligence Later" Is a Deliberate Pattern, Not Just Sequencing (ELI10)

Imagine building a mailbox before you have any mail to put in it. That seems backwards only if you assume the mail arrives instantly. In real projects, "the AI" (Chapter 15's Recommendation Agent) is the slowest, most uncertain, most expensive-to-iterate-on part of the system. Building the mailbox first — the model, the API, the accept/reject workflow — means that by the time the AI is ready to "deliver mail," there's already a working, tested place for it to land, with a stable contract (the model's fields, the API's shape) the AI code has to conform to, rather than the AI's raw uncertain shape leaking into how the database or API were designed. This exact reasoning, generalized, is why itinerary items got `is_ai_generated` in Chapter 8, budget line items got `is_ai_estimated` in Chapter 9, and this chapter's `Recommendation` model exists three chapters before Chapter 15.

### 2.2 Why Accept/Reject Is Modeled as a Status Field, Not a Boolean

You might think "accepted or not" is a simple `is_accepted = BooleanField()`. But a recommendation the user hasn't looked at yet, one they've explicitly accepted, and one they've explicitly rejected are three genuinely different states — a boolean can only represent two. `RecommendationStatus.PENDING` (the default, meaning "AI suggested this, no decision yet") is what makes the "Recommendations" page in Architecture Handbook §7.2 ("Cards with accept/dismiss actions") meaningfully different from a plain checklist.

### 2.3 Why `score` Exists Before Anything Computes It Meaningfully

`score` is a `DecimalField` that Chapter 15's agent will eventually populate with a relevance/confidence value (used for ranking, per Architecture Handbook §9.3: "Ranked, tagged by category"). Adding it now — even though this chapter's seed command will only fill it with placeholder values — means Chapter 15 doesn't need a schema migration just to start writing meaningful numbers into an existing, already-indexed field.

---

## 3. Architecture Decision

**Decision:** `Recommendation.status` uses the same transition-table technique as Chapter 7's `Trip.status`, but with a **much smaller** table — only two real transitions out of `pending` (`accepted`, `rejected`), and both are terminal.

**Alternative considered:** Skip the transition table entirely for something this simple, and just validate `new_status in {"accepted", "rejected"}` inline in the view. **Rejected because:** consistency of pattern has real value across a codebase this large — a future engineer who has already read Chapter 7 immediately recognizes this shape and doesn't need to learn a second, ad hoc way of doing the same kind of thing. The extra few lines of a transition dict cost little and pay off in codebase-wide predictability.

**Decision:** `Recommendation.destination` is a **required** (non-nullable) foreign key with `on_delete=CASCADE` — different from `ItineraryItem.destination`'s optional, `SET_NULL` relationship in Chapter 8.

**Trade-off documented:** a recommendation with no destination at all is close to meaningless (Architecture Handbook §9.3 defines the Recommendation Agent's job as suggesting "restaurants, activities" — always tied to a place), so making the field required here is intentional and different from Chapter 8's item, where an itinerary item can reasonably be a placeholder ("Free morning") with no destination attached. `CASCADE` here does mean deactivating a `Destination` would need to cascade-clean its recommendations too — accepted as correct behavior, since a recommendation for a place no longer in the catalog has nothing left to reference.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Recommendation` model | Needs `Trip` (Ch.7) and `Destination` (Ch.6) to exist |
| Write the accept/reject service + transition table | Must exist before the API is built, mirroring Chapter 7's discipline |
| Write a fake-data seed command | Needed before Chapter 15 can be developed against realistic data, and before this chapter's own API tests have something non-trivial to assert against |
| Build the API | Comes last |

---

## 5. File Structure

```
apps/recommendations/
├── __init__.py
├── apps.py
├── models.py
├── services.py                # accept_recommendation, reject_recommendation
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── seed_fake_recommendations.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_management_commands.py
    └── test_views.py
```

**Why the seed command is named `seed_fake_recommendations`, not just `seed_recommendations`**: the word "fake" is deliberate and permanent in the name — this command's output is explicitly placeholder data for development, never meant to be run in production (where recommendations only ever come from Chapter 15's real agent). Naming it this way makes misuse obvious at a glance, unlike Chapter 6's `seed_destinations`, which seeds genuinely real reference data appropriate for any environment.

---

## 6. Folder Location

All new files under `apps/recommendations/`.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations recommendations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.recommendations
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations recommendations
Migrations for 'recommendations':
  apps/recommendations/migrations/0001_initial.py
    - Create model Recommendation

$ curl http://localhost:8000/api/v1/trips/<trip_id>/recommendations/ -H "Authorization: Bearer <access>"
{
  "results": [
    {
      "id": 1, "category": "activity", "title": "Visit Fushimi Inari Shrine",
      "status": "pending", "score": "0.87", "destination": {"name": "Kyoto", ...}
    }
  ]
}
```

---

## 10. Code

### 10.1 `apps/recommendations/models.py`

```python
from django.db import models

from apps.core.models import TimeStampedModel


class RecommendationCategory(models.TextChoices):
    ACTIVITY = "activity", "Activity"
    RESTAURANT = "restaurant", "Restaurant"
    ACCOMMODATION = "accommodation", "Accommodation"
    TRANSPORT = "transport", "Transport"
    EVENT = "event", "Event"


class RecommendationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Recommendation(TimeStampedModel):
    """
    Read-mostly, AI-populated suggestion tied to a Trip. The data
    layer only — see Chapter 10 for why this exists three chapters
    before Chapter 15's Recommendation Agent actually generates any.
    """
    trip = models.ForeignKey(
        "trips.Trip", on_delete=models.CASCADE, related_name="recommendations",
    )
    destination = models.ForeignKey(
        "destinations.Destination", on_delete=models.CASCADE, related_name="recommendations",
        help_text="Required, unlike ItineraryItem.destination (Chapter 8) — a "
                   "recommendation with no place attached is not meaningful.",
    )
    category = models.CharField(max_length=20, choices=RecommendationCategory.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=RecommendationStatus.choices,
        default=RecommendationStatus.PENDING, db_index=True,
    )
    score = models.DecimalField(
        max_digits=4, decimal_places=3, null=True, blank=True,
        help_text="0.000-1.000 relevance/confidence score. Populated meaningfully "
                   "starting Chapter 15; placeholder values only until then.",
    )
    is_ai_generated = models.BooleanField(
        default=True,
        help_text="Defaults True here (unlike itinerary/budget's False default) "
                   "because, unlike those, a Recommendation with is_ai_generated=False "
                   "is the unusual case — see Chapter 10 Code Walkthrough.",
    )

    class Meta:
        ordering = ["-score", "-created_at"]
        indexes = [
            models.Index(fields=["trip", "status"]),
        ]
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"
```

**Why `is_ai_generated` defaults to `True` here, the opposite of Chapter 8/9's `False` default**: this is a deliberate, explicitly-called-out inversion, not an inconsistency. `ItineraryItem`/`BudgetLineItem` are things a *user* typically creates directly (with the AI as an optional accelerant), so `False` (human-created) is the sensible default. `Recommendation`, by contrast, exists almost entirely *because* of the AI — a user doesn't normally hand-author their own "recommendation to themselves" — so `True` is the sensible default, with `False` reserved for the unusual case of a manually-curated suggestion (perhaps injected by staff, or a future partner-sourced listing per Architecture Handbook §13's marketplace roadmap).

**Why `ordering = ["-score", "-created_at"]`**: this ensures the highest-confidence recommendations surface first by default, with recency as the tiebreaker — directly matching Architecture Handbook §9.3's requirement that Recommendation Agent output be "Ranked."

### 10.2 `apps/recommendations/services.py`

```python
"""
Accept/reject state machine — same transition-table technique as
Chapter 7's Trip status, scaled down to this app's simpler shape.
"""
from apps.core.exceptions import BusinessRuleViolation
from apps.recommendations.models import Recommendation, RecommendationStatus


class InvalidRecommendationTransition(BusinessRuleViolation):
    default_message = "This recommendation has already been decided and cannot be changed."
    default_code = "invalid_recommendation_transition"


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    RecommendationStatus.PENDING: {RecommendationStatus.ACCEPTED, RecommendationStatus.REJECTED},
    RecommendationStatus.ACCEPTED: set(),   # terminal
    RecommendationStatus.REJECTED: set(),   # terminal
}


def _transition(*, recommendation: Recommendation, new_status: str) -> Recommendation:
    allowed = _ALLOWED_TRANSITIONS.get(recommendation.status, set())
    if new_status not in allowed:
        raise InvalidRecommendationTransition()
    recommendation.status = new_status
    recommendation.save(update_fields=["status", "updated_at"])
    return recommendation


def accept_recommendation(*, recommendation: Recommendation) -> Recommendation:
    return _transition(recommendation=recommendation, new_status=RecommendationStatus.ACCEPTED)


def reject_recommendation(*, recommendation: Recommendation) -> Recommendation:
    return _transition(recommendation=recommendation, new_status=RecommendationStatus.REJECTED)
```

**Why `_transition` is a private helper called by two thin public functions, rather than one public `set_recommendation_status(new_status)`**: `accept_recommendation`/`reject_recommendation` give the views (and, more importantly, this app's eventual consumers — Chapter 15's agent doesn't call these, but a future "bulk accept all" feature might) a clear, self-documenting, typo-proof API — you cannot accidentally pass an invalid status string to a function that doesn't accept one as a parameter at all. This is a small but genuine safety improvement over a single generic setter, worth the minor duplication.

### 10.3 `apps/recommendations/management/commands/seed_fake_recommendations.py`

```python
"""
Seeds PLACEHOLDER recommendations for a given trip, for local
development and for Chapter 15's agent development to have
realistic data to work against before the real agent exists.
NEVER run this in production — see Chapter 10 for why the word
"fake" is permanently part of this command's name.
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.destinations.models import Destination
from apps.recommendations.models import Recommendation, RecommendationCategory
from apps.trips.models import Trip

_FAKE_TITLES = {
    RecommendationCategory.ACTIVITY: ["Visit the old town", "Guided walking tour", "Sunset viewpoint hike"],
    RecommendationCategory.RESTAURANT: ["Local noodle house", "Rooftop dinner spot", "Street food market"],
    RecommendationCategory.ACCOMMODATION: ["Boutique riverside hotel", "Budget hostel near center"],
    RecommendationCategory.TRANSPORT: ["Day rail pass", "Bike rental"],
    RecommendationCategory.EVENT: ["Weekend night market", "Local festival"],
}


class Command(BaseCommand):
    help = "Seed FAKE placeholder recommendations for a trip. Development only."

    def add_arguments(self, parser):
        parser.add_argument("trip_id", type=str)
        parser.add_argument("--count", type=int, default=5)

    def handle(self, *args, **options):
        try:
            trip = Trip.objects.get(pk=options["trip_id"])
        except Trip.DoesNotExist:
            raise CommandError(f"No trip found with id {options['trip_id']}")

        destinations = list(trip.destinations.all()) or list(Destination.objects.filter(is_active=True)[:5])
        if not destinations:
            raise CommandError("No destinations available to attach fake recommendations to.")

        created = 0
        for _ in range(options["count"]):
            category = random.choice(list(RecommendationCategory))
            Recommendation.objects.create(
                trip=trip,
                destination=random.choice(destinations),
                category=category,
                title=random.choice(_FAKE_TITLES[category]),
                description="Placeholder recommendation for development — not real AI output.",
                score=Decimal(str(round(random.uniform(0.5, 0.99), 3))),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} fake recommendations for trip {trip.id}."))
```

**Why this command takes a required `trip_id` argument instead of seeding globally like Chapter 6's `seed_destinations`**: recommendations are always trip-scoped, never global reference data — there is no meaningful "seed recommendations for the whole system" operation, only "seed some for this specific trip," which is exactly the shape a future developer or CI fixture-setup step needs.

### 10.4 `apps/recommendations/serializers.py`

```python
from rest_framework import serializers

from apps.destinations.serializers import DestinationSerializer
from apps.recommendations.models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    destination = DestinationSerializer(read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id", "category", "title", "description", "status",
            "score", "is_ai_generated", "destination", "created_at",
        ]
        read_only_fields = fields  # entirely read-only via this serializer —
        # status changes go exclusively through the accept/reject endpoints
```

**Why every field is read-only on this serializer, with no separate write path exposed here at all**: unlike `TripSerializer` (Chapter 7), which accepts real user-authored input, `Recommendation` rows in this chapter are only ever created by the seed command (development) or, from Chapter 15 onward, the AI agent — never directly by a user through this API. The *only* user-initiated write in this entire app is a status transition, which is why `services.py` exposes narrow `accept_recommendation`/`reject_recommendation` functions instead of a general-purpose serializer-backed update endpoint.

### 10.5 `apps/recommendations/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recommendations import services
from apps.recommendations.models import Recommendation
from apps.recommendations.serializers import RecommendationSerializer
from apps.trips.models import Trip


def _get_trip_for_user(trip_pk, user) -> Trip:
    return get_object_or_404(Trip, pk=trip_pk, user=user)


class TripRecommendationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = _get_trip_for_user(trip_pk, request.user)
        queryset = trip.recommendations.select_related("destination")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response(RecommendationSerializer(queryset, many=True).data)


class RecommendationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk, recommendation_pk):
        trip = _get_trip_for_user(trip_pk, request.user)
        recommendation = get_object_or_404(Recommendation, pk=recommendation_pk, trip=trip)
        updated = services.accept_recommendation(recommendation=recommendation)
        return Response(RecommendationSerializer(updated).data)


class RecommendationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk, recommendation_pk):
        trip = _get_trip_for_user(trip_pk, request.user)
        recommendation = get_object_or_404(Recommendation, pk=recommendation_pk, trip=trip)
        updated = services.reject_recommendation(recommendation=recommendation)
        return Response(RecommendationSerializer(updated).data)
```

**Why accept and reject are two separate endpoints/views instead of one `POST /recommendations/{id}/decide/` with a `{"decision": "accept"}` body**: two small, explicit, unambiguous URLs (`/accept/`, `/reject/`) are self-documenting in a way a single generic endpoint with a body parameter isn't — an API consumer (or a glance at the URL log) immediately knows what happened, without needing to inspect the request body. This mirrors the same "explicit over generic" instinct behind Chapter 7's dedicated `/trips/{id}/status/` endpoint, applied here with two endpoints instead of one because there are exactly two meaningful outcomes.

### 10.6 `apps/recommendations/urls.py`

```python
from django.urls import path

from apps.recommendations.views import (
    RecommendationAcceptView,
    RecommendationRejectView,
    TripRecommendationListView,
)

app_name = "recommendations"

urlpatterns = [
    path("<uuid:trip_pk>/recommendations/", TripRecommendationListView.as_view(), name="list"),
    path("<uuid:trip_pk>/recommendations/<int:recommendation_pk>/accept/",
         RecommendationAcceptView.as_view(), name="accept"),
    path("<uuid:trip_pk>/recommendations/<int:recommendation_pk>/reject/",
         RecommendationRejectView.as_view(), name="reject"),
]
```

### 10.7 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.recommendations.urls")),
```

### 10.8 `apps/recommendations/admin.py`

```python
from django.contrib import admin

from apps.recommendations.models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ["title", "trip", "category", "status", "score", "is_ai_generated"]
    list_filter = ["category", "status", "is_ai_generated"]
    search_fields = ["title", "trip__title"]
    readonly_fields = ["created_at", "updated_at"]
```

---

## 11. Code Walkthrough

- **Three apps in a row (`itinerary`, `budget`, `recommendations`) now each carry an `is_ai_*` boolean, but with two different defaults (`False`, `False`, `True`)**: reading these three chapters together tells a coherent story — the default always reflects "which origin is the common case for this specific type of data," decided per-model rather than applied uniformly by rote. This is a good moment to recognize that consistency of *pattern* (always having the flag) doesn't require consistency of *value* (the default) when the underlying reality genuinely differs.
- **The seed command's fake titles are hardcoded English strings, not fetched from anywhere**: this is intentionally throwaway, low-effort data — spending real design effort on "realistic" fake data would be wasted work, since Chapter 15's actual agent output will look nothing like these placeholder strings anyway. The only job of this data is to exercise the API and unblock frontend/agent development, not to look good.
- **`TripRecommendationListView` supports `?status=` filtering, reusing the exact query-param pattern from Chapter 7's trip list (`?status=`) and Chapter 6's destination search (`?search=`)**: another small, deliberate consistency — once a pattern for "optional query-param filter on a list view" is established, repeating it exactly (same param-reading style, same `if status_filter:` guard shape) across apps makes every list endpoint in the project predictable to a new reader.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `InvalidRecommendationTransition` on an accept/reject call | Recommendation already `accepted` or `rejected` — both are terminal states | Expected behavior; a decided recommendation cannot be un-decided through this API (by design — no "undo" endpoint exists yet) |
| `CommandError: No destinations available to attach fake recommendations to` | Ran `seed_fake_recommendations` on a trip with no linked destinations and an empty destinations catalog | Run Chapter 6's `seed_destinations` first, or link destinations to the trip before seeding |
| Recommendations list appears unordered / lowest score first | Forgot that default ordering is `["-score", "-created_at"]` (descending) — a common sign confusion, not a bug | Confirm expectations; this is correct, intended behavior |
| `403`/`404` confusion when testing accept/reject | Using a trip ID that belongs to a different user than the authenticated token | Expected — `_get_trip_for_user` returns 404 for a trip that isn't the caller's, consistent with Chapters 8-9's convention |

---

## 13. Debugging

```bash
# 1. Seed fake data for a real trip and inspect it
docker compose exec web python manage.py shell -c "
from apps.trips.models import Trip
print(Trip.objects.values_list('id', 'title'))
"
docker compose exec web python manage.py seed_fake_recommendations <trip-id> --count 8

# 2. Confirm the transition table end-to-end
docker compose exec web python manage.py shell -c "
from apps.recommendations.models import Recommendation
from apps.recommendations import services
rec = Recommendation.objects.first()
print(rec.status)
services.accept_recommendation(recommendation=rec)
rec.refresh_from_db()
print(rec.status)
try:
    services.reject_recommendation(recommendation=rec)
except Exception as e:
    print('correctly rejected second transition:', e)
"
```

**Rollback strategy:** since `seed_fake_recommendations` is clearly named and scoped to a single trip, cleanup is simple and safe: `Recommendation.objects.filter(trip_id=<trip-id>, description__icontains="Placeholder recommendation").delete()` — the description text itself doubles as a marker distinguishing seeded fake data from anything real, which is worth keeping in mind as a lightweight safety net even without a dedicated `is_seed_data` flag.

---

## 14. Testing

### 14.1 `apps/recommendations/tests/test_services.py`

**Note before the code:** `InvalidRecommendationTransition` is defined directly inside `services.py` (Section 10.2), not a separate `exceptions.py` — this app has exactly one custom exception, so a dedicated exceptions module would be an empty-ceremony file. Import it from `apps.recommendations.services`, not `apps.recommendations.exceptions`.

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations import services
from apps.recommendations.models import Recommendation, RecommendationCategory
from apps.recommendations.services import InvalidRecommendationTransition
from apps.trips.models import Trip

User = get_user_model()


class RecommendationTransitionServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="r@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        destination = Destination.objects.create(name="Kyoto", country="Japan")
        self.recommendation = Recommendation.objects.create(
            trip=trip, destination=destination, category=RecommendationCategory.ACTIVITY, title="Test rec",
        )

    def test_accept_from_pending_succeeds(self):
        updated = services.accept_recommendation(recommendation=self.recommendation)
        self.assertEqual(updated.status, "accepted")

    def test_reject_from_pending_succeeds(self):
        updated = services.reject_recommendation(recommendation=self.recommendation)
        self.assertEqual(updated.status, "rejected")

    def test_accept_after_already_accepted_raises(self):
        services.accept_recommendation(recommendation=self.recommendation)
        with self.assertRaises(InvalidRecommendationTransition):
            services.accept_recommendation(recommendation=self.recommendation)

    def test_reject_after_accepted_raises(self):
        services.accept_recommendation(recommendation=self.recommendation)
        with self.assertRaises(InvalidRecommendationTransition):
            services.reject_recommendation(recommendation=self.recommendation)
```

### 14.2 `apps/recommendations/tests/test_management_commands.py`

```python
from datetime import date
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations.models import Recommendation
from apps.trips.models import Trip

User = get_user_model()


class SeedFakeRecommendationsCommandTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="cmd@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        destination = Destination.objects.create(name="Tokyo", country="Japan")
        self.trip.destinations.add(destination)

    def test_seed_creates_requested_count(self):
        call_command("seed_fake_recommendations", str(self.trip.id), "--count", "4", stdout=StringIO())
        self.assertEqual(Recommendation.objects.filter(trip=self.trip).count(), 4)

    def test_seed_without_destinations_falls_back_to_catalog(self):
        Destination.objects.create(name="Osaka", country="Japan")
        empty_trip = Trip.objects.create(
            user=self.trip.user, title="No dests", start_date=date(2026, 2, 1), end_date=date(2026, 2, 5)
        )
        call_command("seed_fake_recommendations", str(empty_trip.id), "--count", "2", stdout=StringIO())
        self.assertEqual(Recommendation.objects.filter(trip=empty_trip).count(), 2)
```

### 14.3 `apps/recommendations/tests/test_views.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.destinations.models import Destination
from apps.recommendations.models import Recommendation, RecommendationCategory
from apps.trips.models import Trip

User = get_user_model()


class RecommendationAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.stranger = User.objects.create_user(email="stranger@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.owner, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )
        destination = Destination.objects.create(name="Kyoto", country="Japan")
        self.rec = Recommendation.objects.create(
            trip=self.trip, destination=destination, category=RecommendationCategory.ACTIVITY, title="Test rec",
        )
        self.owner_token = self._login("owner@example.com")
        self.stranger_token = self._login("stranger@example.com")

    def _login(self, email):
        response = self.client.post(reverse("accounts:login"), {"email": email, "password": "pass1234"})
        return response.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_list_recommendations(self):
        response = self.client.get(
            reverse("recommendations:list", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_status(self):
        response = self.client.get(
            reverse("recommendations:list", kwargs={"trip_pk": self.trip.pk}) + "?status=accepted",
            **self._auth(self.owner_token),
        )
        self.assertEqual(len(response.data), 0)

    def test_accept_endpoint(self):
        response = self.client.post(
            reverse("recommendations:accept", kwargs={"trip_pk": self.trip.pk, "recommendation_pk": self.rec.pk}),
            **self._auth(self.owner_token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")

    def test_accept_twice_returns_400(self):
        self.client.post(
            reverse("recommendations:accept", kwargs={"trip_pk": self.trip.pk, "recommendation_pk": self.rec.pk}),
            **self._auth(self.owner_token),
        )
        response = self.client.post(
            reverse("recommendations:accept", kwargs={"trip_pk": self.trip.pk, "recommendation_pk": self.rec.pk}),
            **self._auth(self.owner_token),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stranger_gets_404_on_accept(self):
        response = self.client.post(
            reverse("recommendations:accept", kwargs={"trip_pk": self.trip.pk, "recommendation_pk": self.rec.pk}),
            **self._auth(self.stranger_token),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.recommendations -v 2
```

---

## 15. Git Commit

```bash
git add apps/recommendations/
git commit -m "feat(recommendations): data layer + accept/reject workflow (no AI yet)

- Recommendation: required Destination FK (CASCADE) — unlike
  ItineraryItem's optional/SET_NULL relation (Chapter 8), a
  recommendation with no destination isn't meaningful
- is_ai_generated defaults True here (inverse of itinerary/budget's
  False default) — documented as intentional per-model reasoning,
  not inconsistency
- score field added now (placeholder values only) so Chapter 15's
  agent needs no schema migration to start writing real values
- Transition-table state machine (pending -> accepted/rejected, both
  terminal), same technique as Chapter 7's Trip status, scaled down
- seed_fake_recommendations management command: clearly named,
  trip-scoped, unblocks Chapter 15 agent development and this
  chapter's own API tests before real AI exists
- Entirely read-only serializer — the only user-initiated writes in
  this app are the two dedicated accept/reject endpoints
- Full coverage: transition edge cases, seed command, cross-user
  404 enforcement (consistent with Chapters 8-9)

Third and final 'structure before intelligence' data-layer app
before Volume 4 (AI Layer) begins. Chapter 10 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Recommendation.destination` is required (non-nullable), `CASCADE` — confirmed distinct from Chapter 8's optional/`SET_NULL` pattern
- [ ] `is_ai_generated` defaults to `True`, with the reasoning for the flipped default documented inline
- [ ] `score` field exists even though nothing meaningfully populates it yet
- [ ] Transition table covers `pending` → `{accepted, rejected}`, both terminal, verified by a "second transition rejected" test
- [ ] `seed_fake_recommendations` requires a `trip_id`, never seeds globally
- [ ] Accept/reject exposed as two separate, explicit endpoints, not one generic decision endpoint
- [ ] Cross-user access returns 404, consistent with Chapters 8-9
- [ ] All tests passing
- [ ] Commit made
- [ ] **Volume 3 complete** — `itinerary`, `budget`, `recommendations` all built as "structure first" apps, ready for Volume 4 to add real intelligence

---

## 17. Next Chapter Preview

**Chapter 11 — `ai/` Package Foundations** begins Volume 4 and is the most structurally different chapter so far: it introduces the `ai/` package itself (Architecture Handbook §3.3 — deliberately **not** a Django app), the Groq client wrapper, the prompt module structure, and the Pydantic output schemas every future agent will validate against. This is also the first chapter requiring a real external secret (`GROQ_API_KEY`) in `.env`, and the first to test code with **zero** Django dependency at all — plain `pytest`, no `manage.py test`. Say **"Continue to Chapter 11"** when ready.
