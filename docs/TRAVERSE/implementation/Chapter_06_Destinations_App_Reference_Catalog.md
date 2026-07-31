# Chapter 6 — `destinations` App: Reference Catalog

**Volume 2: Identity & Core Domain | Chapter 6 of 29**

> `Destination` is the project's first model with **no** foreign key to `User` at all. It is reference data — shared, catalog-style information about places in the world — not something any individual user owns. This chapter introduces seed data via a management command (not a signal, since there's no per-user event to react to), search/filtering, and the first real use of Chapter 3's `IsStaffOrReadOnly` permission.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Recognize the difference between **user-owned data** (Profile, and soon Trip) and **reference data** (Destination), and model each correctly.
- Write a Django management command to seed reference data reproducibly, instead of relying on manual admin data entry.
- Implement search/filtering on a DRF list endpoint using `django-filter` or manual `Q` objects.
- Apply `IsStaffOrReadOnly` (built in Chapter 3) to protect a catalog from being edited by regular users while staying fully readable.

---

## 2. Theory

### 2.1 User-Owned Data vs. Reference Data (ELI10)

Think of a library. The books on the shelves (Destination) belong to the library, not to any one visitor — everyone reads the same catalog. But your personal borrowing history (Trip, eventually) belongs to *you*. Modeling these the same way would be a mistake: reference data needs no `user` field, no ownership permission, and is edited by staff, not end users. This distinction is why Architecture Handbook §4.4 explicitly calls out that `destinations` "doesn't have a `user` foreign key."

### 2.2 Why Seed Data Belongs In a Management Command, Not Admin Data Entry

Typing 50 cities into the Django admin by hand is not reproducible — a fresh developer's local database, or a freshly built CI database (Chapter 28), would start empty and have no way to get the same data back except by repeating the manual work. A management command is **code**, which means it's version-controlled, reviewable, and re-runnable identically every time.

### 2.3 Why Search Needs Its Own Design Thought, Not Just "Add a Filter"

Chapter 7's `Trip` creation flow will call this search endpoint live, as a user types a destination name. That means: it must be fast (indexed), forgiving of partial/case-insensitive input, and must not require an exact match. Getting this right now saves Chapter 7 from having to work around a bad search API later.

---

## 3. Architecture Decision

**Decision:** `Destination` uses an **integer** primary key (not UUID), because unlike `Trip` (Chapter 7, user data, exposed in personal URLs), `Destination` IDs are not sensitive — there's nothing to protect by hiding sequential IDs for a public list of cities.

**Alternative considered:** Use UUIDs everywhere uniformly for consistency. **Rejected because:** Chapter 3's `UUIDPrimaryKeyModel` was deliberately built as an *optional* mixin, not a default — applying it here would add index/storage overhead and awkward-to-read admin URLs for zero actual security benefit, since destination enumeration isn't a meaningful attack (Section 15 revisits this).

**Decision:** Search matches on a case-insensitive partial match against `name` and `country`, backed by a database index on `name`.

**Trade-off documented:** partial `icontains` search doesn't scale as elegantly as full-text search (Postgres `tsvector`) at very large catalogs (hundreds of thousands of destinations) — accepted for now as a YAGNI call, with a note that if the catalog ever grows that large, this is the exact spot to revisit with Postgres full-text search, without needing to change the API contract.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Destination` model | Nothing else in this chapter can exist without it |
| Add the search index | Must exist before real search queries are tested, or "it's slow" gets misdiagnosed as an app bug instead of a missing index |
| Write the seed command | Needed before the search API can be meaningfully tested — searching an empty table proves nothing |
| Build the read-only-for-most API | Comes last, since it depends on there being real seeded data to query against |

---

## 5. File Structure

```
apps/destinations/
├── __init__.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── seed_destinations.py
├── migrations/
│   └── __init__.py
├── fixtures/
│   └── destinations_seed.json
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_management_commands.py
    └── test_views.py
```

---

## 6. Folder Location

All new files under `apps/destinations/`. The `management/commands/` folder shape is a Django-mandated convention — the command's filename (`seed_destinations.py`) becomes its CLI name (`manage.py seed_destinations`) automatically.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations destinations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_destinations
docker compose exec web python manage.py test apps.destinations
```

---

## 8. Docker Commands

```bash
docker compose exec web python manage.py seed_destinations --dry-run
docker compose restart web
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py seed_destinations
Seeding destinations...
Created: Tokyo, Japan
Created: Kyoto, Japan
Created: Paris, France
Created: Rome, Italy
...
Seed complete. 25 created, 0 updated, 0 skipped.

$ curl "http://localhost:8000/api/v1/destinations/?search=tok"
{
  "count": 1,
  "results": [{"id": 1, "name": "Tokyo", "country": "Japan", ...}]
}
```

---

## 10. Code

### 10.1 `apps/destinations/models.py`

```python
from django.db import models

from apps.core.models import TimeStampedModel


class DestinationType(models.TextChoices):
    CITY = "city", "City"
    REGION = "region", "Region"
    COUNTRY = "country", "Country"
    LANDMARK = "landmark", "Landmark / Point of Interest"


class Destination(TimeStampedModel):
    """
    Reference catalog data. NOT user-owned — deliberately has no
    `user` foreign key. Edited by staff only (see IsStaffOrReadOnly,
    Chapter 3), read by everyone.
    """
    name = models.CharField(max_length=150, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    destination_type = models.CharField(
        max_length=20, choices=DestinationType.choices, default=DestinationType.CITY,
    )
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    average_daily_cost_usd = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Rough average daily cost per traveler, used as a starting "
                   "estimate by the Budget Agent (Chapter 13).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive destinations are hidden from search but not deleted, "
                   "so existing Trips referencing them don't break.",
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["name", "country"], name="unique_destination_per_country"),
        ]
        verbose_name = "Destination"
        verbose_name_plural = "Destinations"

    def __str__(self) -> str:
        return f"{self.name}, {self.country}"
```

**Why `is_active` instead of hard-deleting inactive destinations:** unlike `Profile` (which cascades on user delete), `Destination` may already be referenced by real `Trip`/`ItineraryItem` rows once Chapters 7-8 ship. Hard-deleting a destination someone's real trip points to would either cascade-delete their trip data (bad) or require `SET_NULL` handling everywhere (fragile). Soft-deactivating via `is_active` — filtered out of search, but still present for existing references — sidesteps the whole problem, consistent with the `on_delete=SET_NULL` decision already documented for this exact relationship in Architecture Handbook §5.8.

**Why `UniqueConstraint(fields=["name", "country"])` instead of a unique constraint on `name` alone:** there is more than one real-world "Paris" (Paris, France vs. Paris, Texas) — uniqueness has to be scoped to the pair, not the name alone.

### 10.2 `apps/destinations/management/commands/seed_destinations.py`

```python
"""
Seeds the destinations catalog with a starter set of well-known
travel destinations. Safe to re-run — uses update_or_create, so
running it twice does not create duplicates.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.destinations.models import Destination

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "destinations_seed.json"


class Command(BaseCommand):
    help = "Seed the destinations catalog from fixtures/destinations_seed.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would be created/updated without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        data = json.loads(FIXTURE_PATH.read_text())

        created_count = 0
        updated_count = 0

        self.stdout.write("Seeding destinations...")

        for entry in data:
            if dry_run:
                self.stdout.write(f"Would upsert: {entry['name']}, {entry['country']}")
                continue

            _, created = Destination.objects.update_or_create(
                name=entry["name"],
                country=entry["country"],
                defaults={
                    "destination_type": entry.get("destination_type", "city"),
                    "description": entry.get("description", ""),
                    "latitude": entry.get("latitude"),
                    "longitude": entry.get("longitude"),
                    "average_daily_cost_usd": entry.get("average_daily_cost_usd"),
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created: {entry['name']}, {entry['country']}")
            else:
                updated_count += 1
                self.stdout.write(f"Updated: {entry['name']}, {entry['country']}")

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Seed complete. {created_count} created, {updated_count} updated, 0 skipped."
            ))
```

### 10.3 `apps/destinations/fixtures/destinations_seed.json` (excerpt)

```json
[
  {
    "name": "Tokyo",
    "country": "Japan",
    "destination_type": "city",
    "description": "Japan's bustling capital, blending ultramodern and traditional.",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "average_daily_cost_usd": 120.00
  },
  {
    "name": "Kyoto",
    "country": "Japan",
    "destination_type": "city",
    "description": "Former imperial capital known for temples and gardens.",
    "latitude": 35.0116,
    "longitude": 135.7681,
    "average_daily_cost_usd": 95.00
  },
  {
    "name": "Paris",
    "country": "France",
    "destination_type": "city",
    "description": "The City of Light.",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "average_daily_cost_usd": 140.00
  }
]
```

**Why this fixture is not Django's built-in `loaddata` fixture format:** Django's native fixtures are tied to app labels and PK values, which makes them brittle across environments (a PK collision risk, and awkward to hand-edit). A plain JSON list, consumed by our own `update_or_create` logic, is easier to read, easier to diff in code review, and immune to PK conflicts entirely.

### 10.4 `apps/destinations/serializers.py`

```python
from rest_framework import serializers

from apps.destinations.models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            "id", "name", "country", "destination_type", "description",
            "latitude", "longitude", "average_daily_cost_usd", "is_active",
        ]
        read_only_fields = ["id"]
```

### 10.5 `apps/destinations/views.py`

```python
from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView

from apps.core.permissions import IsStaffOrReadOnly
from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationSerializer


class DestinationListCreateView(ListCreateAPIView):
    serializer_class = DestinationSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        queryset = Destination.objects.filter(is_active=True)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(country__icontains=search)
            )
        destination_type = self.request.query_params.get("type")
        if destination_type:
            queryset = queryset.filter(destination_type=destination_type)
        return queryset


class DestinationDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsStaffOrReadOnly]
```

**Why `get_queryset()` builds the filter manually with `Q` objects instead of pulling in `django-filter` for just two filters:** two simple filters don't yet justify a new dependency. This is a deliberate YAGNI call, revisited explicitly in Section 15 — if filter count grows significantly in a later chapter, `django-filter`'s `FilterSet` becomes the better tool, but not yet.

### 10.6 `apps/destinations/urls.py`

```python
from django.urls import path

from apps.destinations.views import DestinationDetailView, DestinationListCreateView

app_name = "destinations"

urlpatterns = [
    path("", DestinationListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", DestinationDetailView.as_view(), name="detail"),
]
```

### 10.7 `config/urls.py` (addition)

```python
path("api/v1/destinations/", include("apps.destinations.urls")),
```

### 10.8 `apps/destinations/admin.py`

```python
from django.contrib import admin

from apps.destinations.models import Destination


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "destination_type", "average_daily_cost_usd", "is_active"]
    list_filter = ["destination_type", "is_active", "country"]
    search_fields = ["name", "country"]
    ordering = ["name"]
    readonly_fields = ["created_at", "updated_at"]
```

---

## 11. Code Walkthrough

- **`update_or_create` in the seed command, keyed on `(name, country)`**: this makes the command idempotent — running it 10 times produces the same 25 rows, not 250. Idempotency is what makes it safe to run automatically in CI (Chapter 28) and in fresh local setups without anyone needing to remember "did I already seed this?"
- **`IsStaffOrReadOnly` reused unchanged from Chapter 3**: this is the payoff of building it as shared, generic code early — zero new permission logic was needed here, just an import.
- **`is_active=True` filtered in `get_queryset()`, not as a `default_manager` filter like `SoftDeleteManager`**: this is a deliberate inconsistency worth explaining — `SoftDeleteModel`'s manager (Chapter 3) hides deleted rows from *everyone, everywhere, by default*, including staff in the admin. Here, staff explicitly *should* see inactive destinations in the admin (to reactivate them), so filtering only happens in the public-facing API view, not at the model/manager level. Same underlying idea (don't show "removed" things by default), different mechanism, chosen deliberately based on who needs to see what.
- **`DestinationDetailView` supports `RetrieveUpdateDestroy`, gated by the same `IsStaffOrReadOnly`**: any authenticated user can `GET` one destination's detail; only staff can `PATCH`/`DELETE` it — exactly mirroring the list view's split, for consistency a future engineer can predict without re-reading the code.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `django.db.utils.IntegrityError: duplicate key value violates unique constraint "unique_destination_per_country"` | Seed fixture has a genuine duplicate `(name, country)` pair | Fix the fixture JSON — this constraint is working as intended, not a bug |
| Search returns nothing for a destination you know exists | Destination has `is_active=False`, correctly filtered out | Check admin — this is expected behavior for deactivated destinations, not a search bug |
| `403 Forbidden` when a regular (non-staff) user tries `POST /destinations/` | `IsStaffOrReadOnly` correctly denying a non-staff write | Expected — only staff can write; log in as a superuser to test writes |
| `FileNotFoundError` running `seed_destinations` | `fixtures/destinations_seed.json` missing or path resolution wrong (e.g., app moved) | Confirm `FIXTURE_PATH`'s `parents[N]` count matches the actual folder depth from the command file |

---

## 13. Debugging

```bash
# 1. Confirm seed idempotency directly
docker compose exec web python manage.py seed_destinations
docker compose exec web python manage.py seed_destinations
docker compose exec web python manage.py shell -c \
  "from apps.destinations.models import Destination; print(Destination.objects.count())"
# Running the command twice must NOT double the count

# 2. Confirm the unique constraint is actually enforced at the DB level,
#    not just app-level
docker compose exec web python manage.py shell -c "
from apps.destinations.models import Destination
Destination.objects.create(name='Tokyo', country='Japan')
"
# Expected: IntegrityError, if Tokyo/Japan was already seeded

# 3. Confirm search performance uses the index (inspect the query plan)
docker compose exec web python manage.py shell -c "
from django.db import connection
from apps.destinations.models import Destination
list(Destination.objects.filter(name__icontains='tok'))
print(connection.queries[-1]['sql'])
"
```

**Rollback strategy:** since `Destination` is reference data with no user-generated dependents yet at this point in the build, the safe reset is `docker compose exec web python manage.py shell -c "from apps.destinations.models import Destination; Destination.objects.all().delete()"` followed by re-running `seed_destinations` — no cascading risk to worry about yet (that changes once Chapter 7's `Trip` starts referencing destinations, at which point deactivation, not deletion, becomes the only safe operation, exactly as `is_active` already anticipates).

---

## 14. Testing

### 14.1 `apps/destinations/tests/test_models.py`

```python
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.destinations.models import Destination


class DestinationModelTests(TestCase):
    def test_str_representation(self):
        d = Destination.objects.create(name="Rome", country="Italy")
        self.assertEqual(str(d), "Rome, Italy")

    def test_duplicate_name_country_pair_rejected(self):
        Destination.objects.create(name="Rome", country="Italy")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Destination.objects.create(name="Rome", country="Italy")

    def test_same_name_different_country_allowed(self):
        Destination.objects.create(name="Paris", country="France")
        Destination.objects.create(name="Paris", country="United States")
        self.assertEqual(Destination.objects.filter(name="Paris").count(), 2)

    def test_default_is_active_true(self):
        d = Destination.objects.create(name="Lima", country="Peru")
        self.assertTrue(d.is_active)
```

### 14.2 `apps/destinations/tests/test_management_commands.py`

```python
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.destinations.models import Destination


class SeedDestinationsCommandTests(TestCase):
    def test_seed_creates_destinations(self):
        out = StringIO()
        call_command("seed_destinations", stdout=out)
        self.assertGreater(Destination.objects.count(), 0)
        self.assertIn("Seed complete", out.getvalue())

    def test_seed_is_idempotent(self):
        call_command("seed_destinations", stdout=StringIO())
        first_count = Destination.objects.count()
        call_command("seed_destinations", stdout=StringIO())
        second_count = Destination.objects.count()
        self.assertEqual(first_count, second_count)

    def test_dry_run_creates_nothing(self):
        out = StringIO()
        call_command("seed_destinations", "--dry-run", stdout=out)
        self.assertEqual(Destination.objects.count(), 0)
        self.assertIn("Would upsert", out.getvalue())
```

### 14.3 `apps/destinations/tests/test_views.py`

```python
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.destinations.models import Destination

User = get_user_model()


class DestinationListViewTests(APITestCase):
    def setUp(self):
        Destination.objects.create(name="Tokyo", country="Japan")
        Destination.objects.create(name="Kyoto", country="Japan")
        Destination.objects.create(name="Paris", country="France")
        Destination.objects.create(name="Osaka", country="Japan", is_active=False)

        self.user = User.objects.create_user(email="u@example.com", password="pass1234")
        login = self.client.post(
            reverse("accounts:login"), {"email": "u@example.com", "password": "pass1234"}
        )
        self.access = login.data["tokens"]["access"]

        self.staff = User.objects.create_user(
            email="staff@example.com", password="pass1234", is_staff=True
        )
        staff_login = self.client.post(
            reverse("accounts:login"), {"email": "staff@example.com", "password": "pass1234"}
        )
        self.staff_access = staff_login.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_search_matches_partial_case_insensitive(self):
        response = self.client.get(
            reverse("destinations:list-create") + "?search=tok", **self._auth(self.access)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [r["name"] for r in response.data["results"]]
        self.assertIn("Tokyo", names)

    def test_inactive_destinations_excluded_from_search(self):
        response = self.client.get(
            reverse("destinations:list-create") + "?search=osaka", **self._auth(self.access)
        )
        names = [r["name"] for r in response.data["results"]]
        self.assertNotIn("Osaka", names)

    def test_search_by_country(self):
        response = self.client.get(
            reverse("destinations:list-create") + "?search=japan", **self._auth(self.access)
        )
        names = {r["name"] for r in response.data["results"]}
        self.assertEqual(names, {"Tokyo", "Kyoto"})

    def test_regular_user_cannot_create_destination(self):
        response = self.client.post(
            reverse("destinations:list-create"),
            {"name": "Berlin", "country": "Germany"},
            **self._auth(self.access),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_destination(self):
        response = self.client.post(
            reverse("destinations:list-create"),
            {"name": "Berlin", "country": "Germany"},
            **self._auth(self.staff_access),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_user_cannot_read(self):
        response = self.client.get(reverse("destinations:list-create"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.destinations -v 2
```

---

## 15. Git Commit

```bash
git add apps/destinations/ config/urls.py
git commit -m "feat(destinations): reference catalog with seed command and search API

- Destination: no user FK (reference data, not user-owned — see
  Chapter 6 theory), unique (name, country) constraint, is_active
  soft-deactivation instead of hard delete (protects future Trip/
  ItineraryItem references per Architecture Handbook §5.8)
- seed_destinations management command: idempotent via
  update_or_create, --dry-run support, JSON fixture (not Django's
  native fixture format — see rationale in Chapter 6)
- Search via manual Q-object filtering on name/country
  (django-filter deferred as YAGNI until filter count grows)
- IsStaffOrReadOnly (Chapter 3) reused unchanged — zero new
  permission code needed
- Full coverage: model constraints, seed idempotency, search
  correctness, staff-only write enforcement

Chapter 6 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Destination` has no `user` foreign key
- [ ] `UniqueConstraint` on `(name, country)` verified via a failing-transaction test
- [ ] `is_active` used for deactivation; no hard-delete path exposed in the public API
- [ ] `seed_destinations` is idempotent (verified by running it twice in a test)
- [ ] `--dry-run` flag creates zero rows
- [ ] Search is case-insensitive and matches partials on both `name` and `country`
- [ ] Inactive destinations excluded from search results
- [ ] `IsStaffOrReadOnly` correctly blocks non-staff writes (403) and allows staff writes (201)
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 7 — `trips` App: The Central Entity** is where user-owned data and reference data meet for the first time: `Trip` has a `user` foreign key (like `Profile`) *and* a many-to-many relationship to `Destination` (like nothing we've built yet). This is also the first chapter to use Chapter 3's `IsOwner` permission for real, and the first `services.py` file in the project, separating business logic from view logic before it has a chance to sprawl. Say **"Continue to Chapter 7"** when ready.
