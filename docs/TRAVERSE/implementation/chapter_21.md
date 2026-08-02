# Chapter 21 — `documents` App

**Volume 6: Supporting Apps | Chapter 21 of 29**

> Volume 6 begins. This is the first chapter to generate a downloadable artifact (a PDF) rather than only JSON API responses, and the first to build genuinely **public, unauthenticated** access — a shareable link a trip owner can hand to a friend who has no account at all. Every endpoint built since Chapter 7 has relied on `IsOwner` or an equivalent ownership check; this chapter deliberately builds something that works *without* authentication, protected instead by an unguessable secret token — a different security model, built carefully and explicitly, not as a shortcut around the ownership pattern.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Generate a PDF document server-side from structured trip data, without persisting the binary itself.
- Explain why a public-facing "capability token" should never be the same value as a resource's own primary key, and implement that separation correctly.
- Choose the right tool for generating a security-sensitive random value (`secrets`, not `uuid4`), and explain the distinction.
- Build an intentionally different permission model for a genuinely different situation, rather than forcing every endpoint through the same `IsOwner` pattern used everywhere else in the project.

---

## 2. Theory

### 2.1 Why the PDF Is Generated On-Demand, Not Stored (ELI10)

Imagine printing a photo every time someone asks to see it, instead of printing a thousand copies in advance and storing them in a warehouse. A trip's itinerary can change (Chapter 8's edits, Chapter 12's re-runs) — a *stored* PDF would immediately become stale the moment the underlying data changes, and now there'd be a second thing (the file) that needs to stay in sync with the first thing (the database), the exact kind of duplicated-truth problem Architecture Handbook §5.5's normalization principles warn against. Generating the PDF fresh, from the current database state, every time it's requested, means it is *always* accurate by construction — the same reasoning behind not caching `Trip.computed_budget_total` as anything other than a signal-refreshed derived value (Chapter 9).

### 2.2 Why a Share Token Must Never Be the Same as the Document's Own Primary Key (ELI10)

Imagine your house key and your house's street address were the same piece of information — anyone who knew your address could also let themselves in. A resource's *identity* (its primary key, used internally, in authenticated API calls, in the admin) and its *access-granting secret* (the token in a public share link) are conceptually different things, even when both happen to be hard-to-guess values. Keeping them separate means that if a `Document`'s primary key is ever legitimately exposed somewhere else in the system (an authenticated API response, an admin URL), that exposure alone doesn't also leak the public sharing secret.

### 2.3 Why `secrets.token_urlsafe()`, Not Another `uuid4()`

Every ID-bearing model so far (`Trip`, `ChatSession`, `Document` itself) uses `uuid4()` via Chapter 3's `UUIDPrimaryKeyModel` — and `uuid4` values are, in practice, extremely hard to guess too. But Python's `uuid` module is documented and designed around generating *unique* identifiers, not explicitly around generating *security tokens* — while `secrets` is Python's standard library module explicitly built and documented for exactly this purpose: generating values that are safe to use as passwords, API keys, or capability tokens. Using the tool whose stated purpose matches the actual requirement, rather than the tool that happens to produce similarly-shaped output, is a small but real engineering discipline worth internalizing.

---

## 3. Architecture Decision

**Decision:** `Document.share_token` is a separate field, generated via `secrets.token_urlsafe(32)`, distinct from `Document.id` (the `UUIDPrimaryKeyModel` primary key). Public share URLs use `share_token`, never `id`.

**Decision:** PDFs are generated synchronously, in-memory, on each request — no `Document` row represents a PDF export at all; only share links are persisted as `Document` rows. A PDF download is a pure request/response artifact with no corresponding database record.

**Alternative considered:** Store every generated PDF as a file, with a `Document` row tracking it, servable from a URL. **Rejected because:** this reintroduces exactly the staleness problem Section 2.1 describes, for a document that's cheap enough to regenerate on every request (a single trip's itinerary is small) — the added complexity of file storage, cleanup, and cache invalidation isn't justified by the actual cost of generation.

**Decision:** The public share endpoint lives under a distinct URL prefix, `/api/v1/public/share/<token>/`, not nested under `/api/v1/trips/`.

**Why:** every other URL under `/api/v1/trips/` implies "you must be authenticated and own this trip" — mixing a genuinely public, unauthenticated endpoint into that same namespace would be confusing and risks a future engineer accidentally applying `IsAuthenticated` to it out of habit. A distinct, clearly-named prefix makes the different security model visible in the URL structure itself, not just in a permission class buried in the view.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Document` model + migration | Needed before any share link can be created |
| Write `apps/documents/services.py` (token generation, PDF generation) | Needed before views can call either |
| Write `apps/documents/selectors.py` (`get_active_document_by_token`) | Needed before the public view can look anything up |
| Build the three authenticated endpoints (PDF, create link, revoke link) | Comes before the public endpoint, since it needs a real link to exist to test against |
| Build the public share endpoint | Last — the one genuinely new security model in this chapter |

---

## 5. File Structure

```
apps/documents/
├── __init__.py
├── apps.py
├── models.py                    # Document
├── services.py                   # generate_itinerary_pdf, create_share_link, revoke_share_link
├── selectors.py                    # get_active_document_by_token
├── serializers.py
├── views.py                        # TripPDFExportView, ShareLinkCreateView, ShareLinkRevokeView, PublicSharedItineraryView
├── urls.py
├── public_urls.py                   # NEW pattern — separate URLconf for the public prefix
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

**Why `public_urls.py` is a separate file from `urls.py`**: this makes the split between "authenticated trip-owner endpoints" and "public unauthenticated endpoints" visible at the file level, not just inside one `urls.py`'s path list — matching Architecture Decision's URL-prefix reasoning one level deeper, into the codebase structure itself.

---

## 6. Folder Location

New files under `apps/documents/` (already scaffolded empty since Chapter 2).

---

## 7. Terminal Commands

```bash
docker compose exec web pip install reportlab --break-system-packages
# add to requirements/base.txt

docker compose exec web python manage.py makemigrations documents
docker compose exec web python manage.py migrate

docker compose exec web python manage.py test apps.documents -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web
```

---

## 9. Expected Output

```
$ curl -X POST http://localhost:8000/api/v1/trips/<trip_id>/documents/share-link/ \
  -H "Authorization: Bearer <access>"
{"share_url": "/api/v1/public/share/kR8f...", "id": "d4e1...", "is_active": true}

$ curl http://localhost:8000/api/v1/public/share/kR8f.../
{"trip_title": "Japan Adventure", "days": [...]}   # NO Authorization header needed

$ curl -o itinerary.pdf http://localhost:8000/api/v1/trips/<trip_id>/documents/pdf/ \
  -H "Authorization: Bearer <access>"
# downloads a real PDF file
```

---

## 10. Code

### 10.1 `apps/documents/models.py`

```python
import secrets

from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


def _generate_share_token() -> str:
    """
    Uses secrets, not uuid4 — see Chapter 21 Theory §2.3 for why
    the standard library's security-token-purpose module is the
    correct tool here, distinct from every other UUID-based ID in
    this project.
    """
    return secrets.token_urlsafe(32)


class Document(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Represents a shareable link. PDF exports have NO corresponding
    row — see Chapter 21 Architecture Decision for why.
    """
    trip = models.ForeignKey("trips.Trip", on_delete=models.CASCADE, related_name="documents")
    share_token = models.CharField(
        max_length=64, unique=True, db_index=True, default=_generate_share_token,
        help_text="Public capability token. Deliberately NOT the same as `id` "
                   "— see Chapter 21 Theory §2.2.",
    )
    is_active = models.BooleanField(default=True, help_text="Owner can revoke a link by deactivating it.")
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Shared Document Link"
        verbose_name_plural = "Shared Document Links"

    def __str__(self) -> str:
        return f"ShareLink<{self.trip.title}>"

    @property
    def is_valid(self) -> bool:
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
```

**Why `default=_generate_share_token` on the field, not set explicitly at creation time in `services.py`**: Django's field-level `default` (accepting a callable) guarantees a token is generated for *every* `Document`, through *any* creation path — direct `.objects.create()`, the admin, a future data migration — without depending on every caller remembering to pass one. This is the same "make the correct behavior structurally the default" instinct as Chapter 3's `TimeStampedModel` auto-timestamps.

**Why `is_valid` is a property, checking both `is_active` and `expires_at` together, rather than two separate checks scattered wherever a link is validated**: a single source of truth for "is this link currently usable" means the public view (Section 10.5) and any future consumer of this logic can't accidentally check only one of the two conditions and introduce a security gap.

### 10.2 `apps/documents/services.py`

```python
"""
Two genuinely different responsibilities live here: managing share
links (persisted, revocable) and generating PDFs (ephemeral,
regenerated on every request — no persistence at all).
"""
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.documents.models import Document
from apps.trips.models import Trip


def create_share_link(*, trip: Trip) -> Document:
    return Document.objects.create(trip=trip)


def revoke_share_link(*, document: Document) -> Document:
    document.is_active = False
    document.save(update_fields=["is_active", "updated_at"])
    return document


def generate_itinerary_pdf(*, trip: Trip) -> bytes:
    """
    Builds a PDF entirely in memory — nothing touches the filesystem,
    nothing is persisted. Returns raw PDF bytes the view streams
    directly to the client.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(trip.title, styles["Title"]))
    elements.append(Paragraph(f"{trip.start_date} to {trip.end_date}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    for day in trip.itinerary_days.all().order_by("day_number"):
        elements.append(Paragraph(f"Day {day.day_number} — {day.date}", styles["Heading2"]))
        if day.summary:
            elements.append(Paragraph(day.summary, styles["Italic"]))

        rows = [["Time", "Activity", "Est. Cost"]]
        for item in day.items.all().order_by("order"):
            rows.append([
                item.start_time.strftime("%H:%M") if item.start_time else "-",
                item.title,
                f"${item.estimated_cost_usd}" if item.estimated_cost_usd else "-",
            ])
        table = Table(rows, colWidths=[70, 300, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), "#dddddd"),
            ("GRID", (0, 0), (-1, -1), 0.5, "#999999"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))

    doc.build(elements)
    return buffer.getvalue()
```

**Why `generate_itinerary_pdf` takes a `Trip` object directly, not a trip ID**: this function is only ever called from a view that has already fetched and ownership-checked the trip — accepting the ID and re-fetching it internally would duplicate work and, worse, would let this function silently skip the ownership check its caller already performed if it were ever called from a different context. Requiring the already-validated object as input makes the function's safe usage explicit at the call site, not implicit.

### 10.3 `apps/documents/selectors.py`

```python
from apps.documents.models import Document


def get_active_document_by_token(*, token: str) -> Document | None:
    try:
        document = Document.objects.select_related("trip").get(share_token=token)
    except Document.DoesNotExist:
        return None
    return document if document.is_valid else None
```

**Why this returns `None` for an expired/revoked token rather than raising an exception the view would need to catch**: the public view's job is simply "valid token → show the itinerary; anything else → 404" — a `None` return keeps that logic a plain, single `if` check in the view, rather than a `try/except` around a lookup that could fail for two conceptually different reasons (doesn't exist at all vs. exists but is no longer valid) that the view doesn't actually need to distinguish between.

### 10.4 `apps/documents/serializers.py`

```python
from rest_framework import serializers

from apps.documents.models import Document
from apps.itinerary.serializers import ItineraryDaySerializer


class ShareLinkSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "share_url", "is_active", "expires_at", "created_at"]
        read_only_fields = fields

    def get_share_url(self, obj: Document) -> str:
        return f"/api/v1/public/share/{obj.share_token}/"


class PublicItinerarySerializer(serializers.Serializer):
    """
    Deliberately minimal — only what a public, unauthenticated
    visitor should ever see. Never includes budget, AgentRun history,
    or anything else a stranger with just a link shouldn't have
    access to.
    """
    trip_title = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = ItineraryDaySerializer(many=True)
```

**Why `ShareLinkSerializer` never exposes `share_token` directly as its own field, only wrapped inside `share_url`**: this is a small but deliberate detail — the token itself is the sensitive value; exposing it pre-formatted into a full URL (rather than as a raw field a client might mishandle, log, or store separately from context) reduces the surface area for it to leak somewhere unintended.

**Why `PublicItinerarySerializer` is a hand-picked subset of fields, not a reuse of `TripSerializer` (Chapter 7) with some fields hidden**: `TripSerializer` was designed for an *authenticated owner's* view of their own trip — reusing it here and trying to strip fields after the fact is exactly the kind of "forget to hide one sensitive field" mistake this chapter's different security model needs to actively guard against. A serializer built from scratch, listing only what's safe to show a stranger, makes the safe set the explicit, complete picture, not a subtraction from something bigger.

### 10.5 `apps/documents/views.py`

```python
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents import services
from apps.documents.models import Document
from apps.documents.selectors import get_active_document_by_token
from apps.documents.serializers import PublicItinerarySerializer, ShareLinkSerializer
from apps.itinerary.selectors import get_trip_itinerary
from apps.trips.models import Trip


class TripPDFExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        pdf_bytes = services.generate_itinerary_pdf(trip=trip)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{trip.title}-itinerary.pdf"'
        return response


class ShareLinkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        document = services.create_share_link(trip=trip)
        return Response(ShareLinkSerializer(document).data, status=http_status.HTTP_201_CREATED)


class ShareLinkRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_pk, document_pk):
        trip = get_object_or_404(Trip, pk=trip_pk, user=request.user)
        document = get_object_or_404(Document, pk=document_pk, trip=trip)
        updated = services.revoke_share_link(document=document)
        return Response(ShareLinkSerializer(updated).data)


class PublicSharedItineraryView(APIView):
    """
    DELIBERATELY AllowAny — the ONE view in the entire project with
    no authentication at all, protected instead by the unguessable
    share_token in the URL. See Chapter 21 Theory §2.2-2.3.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        document = get_active_document_by_token(token=token)
        if document is None:
            return Response(status=http_status.HTTP_404_NOT_FOUND)

        trip = document.trip
        days = get_trip_itinerary(trip=trip)
        payload = {
            "trip_title": trip.title, "start_date": trip.start_date, "end_date": trip.end_date, "days": days,
        }
        return Response(PublicItinerarySerializer(payload).data)
```

**Why `PublicSharedItineraryView` reuses Chapter 8's `get_trip_itinerary` selector for its N+1-safe query, exactly as every authenticated itinerary view does**: performance discipline doesn't relax just because a view is public — if anything, a public endpoint is more exposed to unpredictable traffic patterns, making the fixed-query-count guarantee from Chapter 8 even more valuable here than in an authenticated context.

**Why an invalid/expired/revoked token returns `404`, matching the project's established convention for "this resource, from your perspective, doesn't exist," rather than a `403`**: unlike Chapter 3's `ResourceNotOwned` reasoning (403, because the *requester's identity* is known and simply lacks permission), there is no requester identity at all here — a stranger with a dead link has no more information-theoretic standing to be told "this exists but you can't have it" than to be told nothing exists, so `404` is both consistent with the project's `IsOwner`-adjacent 403-vs-404 reasoning *and* correct for a context where identity doesn't apply.

### 10.6 `apps/documents/urls.py`

```python
from django.urls import path

from apps.documents.views import ShareLinkCreateView, ShareLinkRevokeView, TripPDFExportView

app_name = "documents"

urlpatterns = [
    path("<uuid:trip_pk>/documents/pdf/", TripPDFExportView.as_view(), name="pdf-export"),
    path("<uuid:trip_pk>/documents/share-link/", ShareLinkCreateView.as_view(), name="share-link-create"),
    path("<uuid:trip_pk>/documents/share-link/<uuid:document_pk>/revoke/",
         ShareLinkRevokeView.as_view(), name="share-link-revoke"),
]
```

### 10.7 `apps/documents/public_urls.py`

```python
from django.urls import path

from apps.documents.views import PublicSharedItineraryView

app_name = "public_documents"

urlpatterns = [
    path("share/<str:token>/", PublicSharedItineraryView.as_view(), name="shared-itinerary"),
]
```

### 10.8 `config/urls.py` (additions)

```python
path("api/v1/trips/", include("apps.documents.urls")),
path("api/v1/public/", include("apps.documents.public_urls")),
```

**Why `<str:token>` in the public URL, not `<uuid:token>`**: `share_token` is a `secrets.token_urlsafe()` string, not a UUID — using Django's `<uuid:...>` path converter here would actually reject every real token (wrong format), a subtle bug worth calling out explicitly since every other ID-based URL in this project up to now used `<uuid:pk>`.

### 10.9 `apps/documents/admin.py`

```python
from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["trip", "is_active", "expires_at", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["trip__title"]
    readonly_fields = ["share_token", "created_at", "updated_at"]
```

---

## 11. Code Walkthrough

- **This chapter's `Document` model represents only share links, never PDFs — worth restating because the app's name ("documents") could suggest both are stored artifacts**: the naming is about the *domain concept* (shareable trip documents), not a 1:1 mapping to "one row per generated file." Recognizing when a model should represent a *capability* (a link that can be revoked) versus an *artifact* (a specific generated file) is a genuinely useful modeling distinction.
- **The public view is the first `APIView` in the entire project using `AllowAny`** — every other view since Chapter 4 has used `IsAuthenticated` as a baseline. Seeing `AllowAny` appear exactly once, deliberately, in a project with dozens of endpoints is itself a useful signal: it should always be rare and always be a conscious choice, never a default someone reaches for out of convenience.
- **`is_valid`'s two checks (`is_active`, `expires_at`) are combined in the model, not duplicated in both the selector and the view**: this is the same "one source of truth for a business rule" instinct behind every prior `services.py`/`selectors.py` decision in this project, just expressed as a model property this time since the check is simple enough not to need its own function.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `404` on a public share link you're sure is valid | Used `<uuid:token>` instead of `<str:token>` in the URL pattern, rejecting the real token format | Confirm `public_urls.py` uses `<str:token>`, not `<uuid:token>` |
| PDF download returns a 0-byte or corrupted file | `doc.build(elements)` never called, or `buffer.getvalue()` read before `build()` completes | Confirm the exact order in `generate_itinerary_pdf`: build first, then read the buffer |
| Revoked link still appears accessible | Confusing `Document.objects.get()`'s success (row exists) with actual validity | Always route lookups through `get_active_document_by_token`, never a raw `Document.objects.get(share_token=...)` |
| A stranger can see budget/AI-run data through a share link | Someone extended `PublicItinerarySerializer` carelessly, or swapped it for `TripSerializer` | `PublicItinerarySerializer` must remain a deliberately hand-picked, minimal field set — never reuse an authenticated-context serializer here |

---

## 13. Debugging

```bash
# 1. Confirm token generation actually uses `secrets`, not uuid, by inspecting real values
docker compose exec web python manage.py shell -c "
from apps.documents.models import Document
from apps.trips.models import Trip
trip = Trip.objects.first()
doc = Document.objects.create(trip=trip)
print(doc.id)           # a UUID
print(doc.share_token)  # a secrets.token_urlsafe string — visibly different shape
"

# 2. Confirm a revoked link is actually rejected
docker compose exec web python manage.py shell -c "
from apps.documents import services
from apps.documents.selectors import get_active_document_by_token
from apps.trips.models import Trip
trip = Trip.objects.first()
doc = services.create_share_link(trip=trip)
print(get_active_document_by_token(token=doc.share_token) is not None)  # True
services.revoke_share_link(document=doc)
print(get_active_document_by_token(token=doc.share_token) is not None)  # False
"
```

**Rollback strategy:** revoking a compromised or mistakenly-shared link is instantaneous (`is_active=False`) and requires no data migration — the entire point of building revocation as a simple flag rather than requiring link deletion.

---

## 14. Testing

### 14.1 `apps/documents/tests/test_models.py`

```python
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.documents.models import Document
from apps.trips.models import Trip

User = get_user_model()


class DocumentModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="d@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))

    def test_share_token_generated_automatically(self):
        doc = Document.objects.create(trip=self.trip)
        self.assertTrue(doc.share_token)
        self.assertNotEqual(str(doc.id), doc.share_token)

    def test_two_documents_never_share_a_token(self):
        doc1 = Document.objects.create(trip=self.trip)
        doc2 = Document.objects.create(trip=self.trip)
        self.assertNotEqual(doc1.share_token, doc2.share_token)

    def test_is_valid_true_by_default(self):
        doc = Document.objects.create(trip=self.trip)
        self.assertTrue(doc.is_valid)

    def test_is_valid_false_when_inactive(self):
        doc = Document.objects.create(trip=self.trip, is_active=False)
        self.assertFalse(doc.is_valid)

    def test_is_valid_false_when_expired(self):
        doc = Document.objects.create(trip=self.trip, expires_at=timezone.now() - timedelta(days=1))
        self.assertFalse(doc.is_valid)
```

### 14.2 `apps/documents/tests/test_services.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.documents import services
from apps.itinerary.models import ItineraryDay
from apps.itinerary import services as itinerary_services
from apps.trips.models import Trip

User = get_user_model()


class GenerateItineraryPdfTests(TestCase):
    def test_pdf_bytes_start_with_pdf_magic_number(self):
        user = User.objects.create_user(email="pdf@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Test Trip", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))
        day = ItineraryDay.objects.create(trip=trip, date=date(2026, 6, 1), day_number=1)
        itinerary_services.add_item_to_day(day=day, title="Arrive")

        pdf_bytes = services.generate_itinerary_pdf(trip=trip)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_handles_trip_with_no_itinerary(self):
        user = User.objects.create_user(email="empty@example.com", password="pass1234")
        trip = Trip.objects.create(user=user, title="Empty Trip", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))
        pdf_bytes = services.generate_itinerary_pdf(trip=trip)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class ShareLinkServiceTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="s@example.com", password="pass1234")
        self.trip = Trip.objects.create(user=user, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 3))

    def test_revoke_sets_is_active_false(self):
        doc = services.create_share_link(trip=self.trip)
        self.assertTrue(doc.is_active)
        services.revoke_share_link(document=doc)
        doc.refresh_from_db()
        self.assertFalse(doc.is_active)
```

### 14.3 `apps/documents/tests/test_views.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents import services
from apps.trips.models import Trip

User = get_user_model()


class DocumentViewTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.stranger = User.objects.create_user(email="stranger@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.owner, title="Test", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1),
        )
        self.owner_token = self._login("owner@example.com")
        self.stranger_token = self._login("stranger@example.com")

    def _login(self, email):
        response = self.client.post(reverse("accounts:login"), {"email": email, "password": "pass1234"})
        return response.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_pdf_export_returns_pdf_content_type(self):
        response = self.client.get(
            reverse("documents:pdf-export", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_stranger_cannot_export_pdf(self):
        response = self.client.get(
            reverse("documents:pdf-export", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.stranger_token)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_share_link_returns_public_url(self):
        response = self.client.post(
            reverse("documents:share-link-create", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("/api/v1/public/share/", response.data["share_url"])

    def test_public_endpoint_requires_no_authentication(self):
        document = services.create_share_link(trip=self.trip)
        response = self.client.get(
            reverse("public_documents:shared-itinerary", kwargs={"token": document.share_token})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["trip_title"], "Test")

    def test_public_endpoint_rejects_revoked_link(self):
        document = services.create_share_link(trip=self.trip)
        services.revoke_share_link(document=document)
        response = self.client.get(
            reverse("public_documents:shared-itinerary", kwargs={"token": document.share_token})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_endpoint_rejects_garbage_token(self):
        response = self.client.get(
            reverse("public_documents:shared-itinerary", kwargs={"token": "not-a-real-token"})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_requires_ownership(self):
        document = services.create_share_link(trip=self.trip)
        response = self.client.post(
            reverse("documents:share-link-revoke", kwargs={"trip_pk": self.trip.pk, "document_pk": document.pk}),
            **self._auth(self.stranger_token),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.documents -v 2
```

---

## 15. Git Commit

```bash
git add apps/documents/ config/urls.py requirements/base.txt
git commit -m "feat(documents): PDF export + shareable links, project's first public endpoint

- Document model represents ONLY share links, never PDFs — PDFs are
  generated fully in-memory on every request, no persistence, no
  staleness risk (same reasoning as Trip.computed_budget_total never
  being anything but signal-derived)
- share_token generated via secrets.token_urlsafe(32), NOT uuid4 —
  deliberately distinct from Document.id (UUIDPrimaryKeyModel);
  never conflate a resource's identity with its access-granting
  secret (Chapter 21 Theory §2.2-2.3)
- PublicSharedItineraryView: the ONLY AllowAny view in the entire
  project — protected by an unguessable token instead of
  authentication; hand-built minimal PublicItinerarySerializer,
  deliberately NOT a trimmed-down TripSerializer, to make the safe
  field set explicit rather than subtractive
- Public URLs live under a distinct /api/v1/public/ prefix, separate
  urls.py file (public_urls.py) — the different security model is
  visible in the codebase structure, not just a permission_classes
  line
- <str:token>, not <uuid:token> — share_token isn't UUID-shaped;
  flagged explicitly since every prior ID-based URL used <uuid:pk>
- Revoked/expired links return 404 (consistent with the project's
  established no-identity-context 404 convention), never 403
- Reuses Chapter 8's N+1-safe get_trip_itinerary() selector even in
  the public view — performance discipline doesn't relax for public
  endpoints, if anything it matters more

Volume 6 begins. Chapter 21 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Document.share_token` is generated via `secrets.token_urlsafe`, distinct from `id`, verified never equal in tests
- [ ] PDFs have zero corresponding database rows; `generate_itinerary_pdf` produces valid PDF bytes (`%PDF` magic number) even for an empty itinerary
- [ ] `PublicSharedItineraryView` is the project's only `AllowAny` view — confirmed by inspection
- [ ] Public URL uses `<str:token>`, not `<uuid:token>`
- [ ] Revoked and expired links both correctly rejected via `is_valid`, tested separately
- [ ] `PublicItinerarySerializer` is hand-built and minimal, never a reused/trimmed authenticated serializer
- [ ] Ownership enforced on all three authenticated endpoints (PDF export, create link, revoke link) — cross-user access returns 404
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 22 — `notifications` App** builds outbound notification dispatch (starting with email), the first genuinely one-way, fire-and-forget communication pattern in the project — no response to wait for, no ownership check on the receiving end (the recipient is simply whoever the triggering event names), and the first chapter to seriously grapple with what happens when the destination (an email provider) is unavailable, distinct from every retry/fallback pattern built so far for LLM calls specifically. Say **"Continue to Chapter 22"** when ready.
