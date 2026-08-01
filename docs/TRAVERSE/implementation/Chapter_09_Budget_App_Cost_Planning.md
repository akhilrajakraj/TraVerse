# Chapter 9 — `budget` App: Cost Planning

**Volume 3: Trip Sub-Domains | Chapter 9 of 29**

> `Budget` mirrors Chapter 5's one-to-one `Profile`/`User` shape (one `Budget` per `Trip`), and `BudgetLineItem` mirrors Chapter 8's many-to-one `ItineraryItem`/`ItineraryDay` shape (many line items per budget). What's new here is the payoff of a decision made all the way back in Chapter 7: `Trip.computed_budget_total` finally gets written to, via a signal that recalculates it using an aggregation query every time a line item changes. This is the first chapter to combine a signal (Chapter 5's pattern) with `Sum` aggregation.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Model a one-to-one child of `Trip` (`Budget`) and a one-to-many child of that child (`BudgetLineItem`), correctly distinguishing this from Chapter 8's two-level pattern.
- Use Django's aggregation API (`Sum`, `Coalesce`) to compute a total safely, including the empty-queryset edge case that trips up almost everyone the first time.
- Wire a signal that keeps a denormalized field (`Trip.computed_budget_total`) in sync automatically, closing the loop Architecture Handbook ADR-7 opened in Chapter 7.
- Enforce a non-negative amount constraint at both validation and database level, following the same defense-in-depth pattern as Chapter 7's date range rule.

---

## 2. Theory

### 2.1 Why `Budget` Is Its Own Model, Not Just Fields on `Trip` (ELI10)

You could imagine cramming "total budget," "currency," and "notes" directly onto `Trip`. But budget has its own lifecycle (a user might set an overall budget cap before any line items exist), its own validation rules (a total that shouldn't go negative), and — most importantly — it's the natural parent for `BudgetLineItem` rows, exactly the same reasoning Architecture Handbook §4.4 gives for why `budget` is separate from `trips` in the first place: "kept separate from itinerary because budget can be edited independently and has different validation rules."

### 2.2 Why `Trip.computed_budget_total` Is Cached Instead of Computed Live Every Time (ELI10)

Imagine a school scoreboard that recalculates the total score by re-adding every single point scored all season, every time someone glances at it. That's wasteful if the scoreboard is checked constantly (Architecture Handbook's dashboard, showing "my active trips" with totals). Instead, the scoreboard is updated once each time a new point is scored, and just *displayed* the rest of the time. `Trip.computed_budget_total` works the same way: updated once whenever a `BudgetLineItem` changes, then just read cheaply everywhere else (the trip list in Chapter 7, future analytics in Chapter 24).

### 2.3 Why This Requires Extra Care With Aggregation

`Sum("amount")` on an empty queryset (a trip with zero line items so far) returns `None` in Django, not `0`. If this isn't handled, `Trip.computed_budget_total` would flip between a real number and `None` depending on whether any line items exist yet — a classic, easy-to-miss bug. Django's `Coalesce` function fixes this by supplying a fallback value when the aggregation result is `None`.

---

## 3. Architecture Decision

**Decision:** `Budget.trip` is a `OneToOneField` with `on_delete=CASCADE`, auto-created via a `post_save` signal on `Trip`, the same pattern as Chapter 5's `Profile`/`User` signal — not lazily created on first access.

**Why the same pattern, not a different one:** consistency has real value here — any engineer who understood Chapter 5's signal already understands this one. Architecture Handbook §5.8 already documented this exact relationship (`Budget.trip` unique, `CASCADE`) as a planned constraint; this chapter simply implements it.

**Decision:** `Trip.computed_budget_total` is recalculated via a signal on `BudgetLineItem`'s `post_save` **and** `post_delete`, not `post_save` alone.

**Alternative considered:** Recalculate only on save, and rely on `CASCADE` handling deletes "automatically." **Rejected because:** deleting a line item changes the correct total just as much as creating one does — `post_save` alone would leave `computed_budget_total` stale (too high) after any line item deletion, silently wrong until the next unrelated save happened to trigger a refresh.

**Decision:** `BudgetLineItem.amount` has a DB `CheckConstraint(amount__gte=0)`, exactly matching Architecture Handbook §5.7's stated constraint, plus serializer-level validation for a friendly error message.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Budget` model | Needs `Trip` (Ch.7) to exist |
| Define `BudgetLineItem` model | Needs `Budget` (this chapter) to exist |
| Write the signal auto-creating `Budget` on `Trip` creation | Must exist before line items can be added to a real budget in tests |
| Write the recalculation signal + selector | Must exist before the API exposes `computed_budget_total`, or the field would always show `None` |
| Build the API | Comes last, depends on everything above already working |

---

## 5. File Structure

```
apps/budget/
├── __init__.py
├── apps.py                  # gains a ready() method, same pattern as profiles
├── models.py
├── signals.py                 # create_budget_on_trip_creation, recalculate_trip_budget_total
├── selectors.py                # get_budget_summary (aggregation)
├── services.py                 # add_line_item, delete_line_item
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_signals.py
    ├── test_selectors.py
    └── test_views.py
```

---

## 6. Folder Location

All new files under `apps/budget/`. One existing file touched outside this app: none — unlike Chapter 5, `Trip` (Chapter 7) does not need any edits, since `computed_budget_total` was already added there in anticipation of this exact chapter.

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations budget
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.budget
```

---

## 8. Docker Commands

```bash
docker compose restart web   # required — signal registration happens at app load, same as Chapter 5
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations budget
Migrations for 'budget':
  apps/budget/migrations/0001_initial.py
    - Create model Budget
    - Create model BudgetLineItem

$ docker compose exec web python manage.py shell -c "
from apps.trips.models import Trip
trip = Trip.objects.first()
print(hasattr(trip, 'budget'), trip.budget.total_amount)
"
True 0.00
```

---

## 10. Code

### 10.1 `apps/budget/models.py`

```python
from django.db import models

from apps.core.models import TimeStampedModel


class BudgetCategory(models.TextChoices):
    ACCOMMODATION = "accommodation", "Accommodation"
    TRANSPORT = "transport", "Transport"
    FOOD = "food", "Food & Dining"
    ACTIVITIES = "activities", "Activities & Tours"
    SHOPPING = "shopping", "Shopping"
    MISC = "misc", "Miscellaneous"


class Budget(TimeStampedModel):
    """
    One-to-one with Trip, same pattern as Profile/User (Chapter 5).
    Auto-created via signal — never created manually in normal flow.
    """
    trip = models.OneToOneField(
        "trips.Trip", on_delete=models.CASCADE, related_name="budget",
    )
    currency = models.CharField(max_length=3, default="USD")
    planned_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional user-set target/cap, distinct from the "
                   "computed actual total of all line items.",
    )

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"

    def __str__(self) -> str:
        return f"Budget<{self.trip.title}>"


class BudgetLineItem(TimeStampedModel):
    """
    A single cost line. Many-to-one with Budget, same shape as
    ItineraryItem/ItineraryDay (Chapter 8).
    """
    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE, related_name="line_items",
    )
    category = models.CharField(max_length=20, choices=BudgetCategory.choices)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    is_ai_estimated = models.BooleanField(
        default=False,
        help_text="True for line items created by Chapter 13's Budget Agent, "
                   "False for a user-entered actual cost — same distinguishing "
                   "pattern as ItineraryItem.is_ai_generated (Chapter 8).",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["budget", "category"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name="budget_line_item_amount_gte_0"),
        ]
        verbose_name = "Budget Line Item"
        verbose_name_plural = "Budget Line Items"

    def __str__(self) -> str:
        return f"{self.description}: {self.amount} ({self.category})"
```

**Why `planned_total` and the computed actual total (from line items) are kept as two distinct concepts, not one field:** a user might want to say "I want to spend at most $2000 on this trip" (a target, `planned_total`) while the running actual total from real line items might currently be $1400 or $2400 — collapsing these into one field would make it impossible to show "you're $600 under budget" or "you're $400 over," a genuinely useful comparison Chapter 24's analytics will eventually surface.

### 10.2 `apps/budget/signals.py`

```python
"""
Two signals here, doing two related but distinct jobs:
1. create_budget_on_trip_creation — mirrors Chapter 5's Profile
   pattern exactly (post_save on Trip, created=True guard).
2. recalculate_trip_budget_total — new pattern: reacts to BOTH
   post_save AND post_delete on BudgetLineItem, since either can
   change the correct total (see Chapter 9 Theory §2.3 and the
   Architecture Decision on why post_save alone is insufficient).
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.budget.models import Budget, BudgetLineItem
from apps.budget.selectors import calculate_budget_total


@receiver(post_save, sender="trips.Trip")
def create_budget_on_trip_creation(sender, instance, created, **kwargs):
    if created:
        Budget.objects.create(trip=instance)


@receiver(post_save, sender=BudgetLineItem)
@receiver(post_delete, sender=BudgetLineItem)
def recalculate_trip_budget_total(sender, instance, **kwargs):
    budget = instance.budget
    trip = budget.trip
    trip.computed_budget_total = calculate_budget_total(budget=budget)
    trip.save(update_fields=["computed_budget_total", "updated_at"])
```

**Why `sender="trips.Trip"` is a string here, following the exact same pattern Chapter 5 used for `settings.AUTH_USER_MODEL`:** decoupling — `apps.budget.signals` never needs a hard import of `apps.trips.models.Trip`, keeping the dependency direction one-way (budget depends on trips conceptually, but doesn't need to import its model class directly to listen for its signal).

**Why one function is decorated with both `@receiver(post_save, ...)` and `@receiver(post_delete, ...)` stacked together:** both events require *exactly* the same reaction — recompute the total from scratch. Writing two nearly-identical functions would violate DRY for no benefit; Python's decorator stacking lets one function serve as the handler for both signals cleanly.

**Why the signal recalculates the total *from scratch* (via `calculate_budget_total`) rather than incrementally adding/subtracting the changed line item's amount:** incremental updates (`total += new_amount` or `total -= deleted_amount`) are faster but fragile — if a line item's amount is *edited* (not just created or deleted), an incremental approach would need yet another special case, and any missed edge case (a failed transaction, a bulk operation bypassing the signal) would let the cached total drift permanently out of sync with reality. Recomputing from scratch via a single aggregation query is slightly more expensive per write but **cannot drift** — it is always, by construction, exactly equal to summing the real rows, an important reliability property directly connected to Architecture Handbook ADR-7's "mitigated with a scheduled reconciliation task" note (this signal *is* effectively that reconciliation, running on every relevant write instead of on a schedule).

### 10.3 `apps/budget/apps.py`

```python
from django.apps import AppConfig


class BudgetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.budget"
    verbose_name = "Budget"

    def ready(self):
        import apps.budget.signals  # noqa: F401
```

### 10.4 `apps/budget/selectors.py`

```python
"""
Read-optimized / aggregation queries for the budget app.
"""
from decimal import Decimal

from django.db.models import DecimalField, Sum
from django.db.models.functions import Coalesce

from apps.budget.models import Budget, BudgetLineItem


def calculate_budget_total(*, budget: Budget) -> Decimal:
    """
    Sums every line item's amount for a budget. Uses Coalesce to
    return Decimal('0.00') instead of None when there are zero line
    items — see Chapter 9 Theory §2.3 for why this matters.
    """
    result = budget.line_items.aggregate(
        total=Coalesce(
            Sum("amount"),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        )
    )
    return result["total"]


def get_budget_summary(*, budget: Budget) -> dict:
    """
    Returns a full breakdown: total, planned vs actual comparison,
    and per-category subtotals — all in 2 queries total regardless
    of how many line items or categories exist.
    """
    total = calculate_budget_total(budget=budget)
    by_category = (
        budget.line_items
        .values("category")
        .annotate(subtotal=Coalesce(
            Sum("amount"), Decimal("0.00"),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        ))
        .order_by("category")
    )
    remaining = (budget.planned_total - total) if budget.planned_total is not None else None

    return {
        "currency": budget.currency,
        "planned_total": budget.planned_total,
        "actual_total": total,
        "remaining": remaining,
        "by_category": list(by_category),
    }
```

**Why `get_budget_summary` costs only 2 queries, not more, despite computing three different things (total, per-category breakdown, remaining)**: `remaining` is pure Python arithmetic on values already fetched, costing zero extra queries. `total` and `by_category` are each one aggregation query — this is worth tracing through explicitly, the same discipline as Chapter 8's N+1 proof, just applied to aggregation instead of nested relations.

### 10.5 `apps/budget/services.py`

```python
"""
Write-side operations for budget line items. Thin here compared to
Chapter 7/8's services.py, because the interesting logic (keeping
the total in sync) already lives in the signal, not here — adding a
line item is otherwise a simple, direct creation.
"""
from apps.budget.models import Budget, BudgetLineItem


def add_line_item(*, budget: Budget, category: str, description: str,
                   amount, is_ai_estimated: bool = False) -> BudgetLineItem:
    return BudgetLineItem.objects.create(
        budget=budget, category=category, description=description,
        amount=amount, is_ai_estimated=is_ai_estimated,
    )


def delete_line_item(*, line_item: BudgetLineItem) -> None:
    line_item.delete()
```

**Why `delete_line_item` exists as a one-line wrapper instead of just calling `.delete()` directly from the view:** consistency of interface — every mutating operation on a budget goes through `services.py`, so a future engineer reading `views.py` never has to wonder "is this one of the operations that goes through the service layer, or not?" The answer is always yes, even when the wrapped logic is trivial.

### 10.6 `apps/budget/serializers.py`

```python
from rest_framework import serializers

from apps.budget.models import Budget, BudgetLineItem


class BudgetLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetLineItem
        fields = ["id", "category", "description", "amount", "is_ai_estimated", "created_at"]
        read_only_fields = ["id", "is_ai_estimated", "created_at"]

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("amount must not be negative.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    line_items = BudgetLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "currency", "planned_total", "line_items"]
        read_only_fields = ["id"]


class BudgetSummarySerializer(serializers.Serializer):
    currency = serializers.CharField()
    planned_total = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    actual_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    by_category = serializers.ListField(child=serializers.DictField())
```

**Why `BudgetSummarySerializer` is a plain `Serializer`, not a `ModelSerializer`**: `get_budget_summary()` returns a plain dict shaped by aggregation, not a model instance — there is no single model this data maps to one-to-one, so a `ModelSerializer` doesn't apply. This is the correct, standard DRF pattern for serializing computed/aggregated data rather than a direct model representation.

### 10.7 `apps/budget/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.budget import services
from apps.budget.models import Budget, BudgetLineItem
from apps.budget.selectors import get_budget_summary
from apps.budget.serializers import (
    BudgetLineItemSerializer,
    BudgetSerializer,
    BudgetSummarySerializer,
)
from apps.trips.models import Trip


def _get_budget_for_user(trip_pk, user) -> Budget:
    trip = get_object_or_404(Trip, pk=trip_pk, user=user)
    return trip.budget


class TripBudgetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        return Response(BudgetSerializer(budget).data)

    def patch(self, request, trip_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        if "planned_total" in request.data:
            budget.planned_total = request.data["planned_total"]
            budget.save(update_fields=["planned_total", "updated_at"])
        return Response(BudgetSerializer(budget).data)


class TripBudgetSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        summary = get_budget_summary(budget=budget)
        return Response(BudgetSummarySerializer(summary).data)


class BudgetLineItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        return Response(BudgetLineItemSerializer(budget.line_items.all(), many=True).data)

    def post(self, request, trip_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        serializer = BudgetLineItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line_item = services.add_line_item(budget=budget, **serializer.validated_data)
        return Response(BudgetLineItemSerializer(line_item).data, status=http_status.HTTP_201_CREATED)


class BudgetLineItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, trip_pk, line_item_pk):
        budget = _get_budget_for_user(trip_pk, request.user)
        line_item = get_object_or_404(BudgetLineItem, pk=line_item_pk, budget=budget)
        services.delete_line_item(line_item=line_item)
        return Response(status=http_status.HTTP_204_NO_CONTENT)
```

**Why `_get_budget_for_user` is a private module-level helper, not a mixin or a class method**: it's used identically across four separate view classes in this file. A small shared function keeps that ownership-scoping logic in exactly one place, following the same 404-not-403 convention Chapter 8 already established for itinerary access (a trip that isn't yours simply doesn't resolve, for the same documented reason).

### 10.8 `apps/budget/urls.py`

```python
from django.urls import path

from apps.budget.views import (
    BudgetLineItemDetailView,
    BudgetLineItemListCreateView,
    TripBudgetSummaryView,
    TripBudgetView,
)

app_name = "budget"

urlpatterns = [
    path("<uuid:trip_pk>/budget/", TripBudgetView.as_view(), name="detail"),
    path("<uuid:trip_pk>/budget/summary/", TripBudgetSummaryView.as_view(), name="summary"),
    path("<uuid:trip_pk>/budget/line-items/", BudgetLineItemListCreateView.as_view(), name="line-items"),
    path("<uuid:trip_pk>/budget/line-items/<int:line_item_pk>/",
         BudgetLineItemDetailView.as_view(), name="line-item-detail"),
]
```

### 10.9 `config/urls.py` (addition)

```python
path("api/v1/trips/", include("apps.budget.urls")),
```

### 10.10 `apps/budget/admin.py`

```python
from django.contrib import admin

from apps.budget.models import Budget, BudgetLineItem


class BudgetLineItemInline(admin.TabularInline):
    model = BudgetLineItem
    extra = 0
    fields = ["category", "description", "amount", "is_ai_estimated"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["trip", "currency", "planned_total"]
    search_fields = ["trip__title"]
    inlines = [BudgetLineItemInline]
```

---

## 11. Code Walkthrough

- **`calculate_budget_total` is called from both the signal (Section 10.2) and the summary selector (Section 10.4)**: one function, two call sites — the signal uses it to keep `Trip.computed_budget_total` fresh on every write; the summary selector uses it to answer a live read. Both always agree, because both ultimately run the same aggregation query — there is no way for the "cached" and "live" numbers to diverge, which is precisely the guarantee Architecture Handbook ADR-7 asked for.
- **`Coalesce(Sum("amount"), Decimal("0.00"), output_field=...)`**: the `output_field` argument is required here, not optional — without it, Django cannot always correctly infer the resulting field's type when combining a nullable aggregate with a literal default, and omitting it is a common source of a cryptic `FieldError` that this code sidesteps entirely.
- **`BudgetLineItemSerializer.validate_amount` duplicates the DB `CheckConstraint`'s rule in Python**: same defense-in-depth reasoning as Chapter 7's date range validation — the serializer gives an immediate, friendly `400` response; the DB constraint is the unconditional last line of defense against any code path that might bypass the serializer entirely.
- **`TripBudgetView.patch` only ever touches `planned_total`, never `line_items`**: this is deliberate scope-limiting — updating the target/cap and adding/removing individual cost lines are different operations with different endpoints (`/budget/` vs `/budget/line-items/`), avoiding an overloaded, ambiguous single endpoint that tries to do both at once.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Trip.computed_budget_total` stays `None` forever | Signal not connected (forgot `ready()`, or stale process) — identical symptom class to Chapter 5 | `docker compose restart web` after confirming `BudgetConfig.ready()` imports `signals` |
| `django.db.utils.IntegrityError` on `budget_line_item_amount_gte_0` | Something tried to insert a negative amount, bypassing the serializer | Expected — DB constraint working correctly; check what code path skipped `services.add_line_item` |
| `FieldError: Expression contains mixed types` | `Coalesce` used without an explicit `output_field` | Add `output_field=DecimalField(...)` exactly as shown in 10.4 |
| Total looks correct after creation but wrong after deleting a line item | Signal only registered for `post_save`, not `post_delete` | Confirm both decorators are stacked on `recalculate_trip_budget_total` as shown |

---

## 13. Debugging

```bash
# 1. Confirm both signals are connected
docker compose exec web python manage.py shell -c "
from django.db.models.signals import post_save, post_delete
from apps.budget.models import BudgetLineItem
print([r.__name__ for r in post_save._live_receivers(sender=BudgetLineItem)])
print([r.__name__ for r in post_delete._live_receivers(sender=BudgetLineItem)])
"

# 2. Manually verify total recalculation end-to-end
docker compose exec web python manage.py shell -c "
from apps.trips.models import Trip
from apps.budget import services
trip = Trip.objects.first()
print('before:', trip.computed_budget_total)
item = services.add_line_item(budget=trip.budget, category='food', description='Test', amount='50.00')
trip.refresh_from_db()
print('after add:', trip.computed_budget_total)
services.delete_line_item(line_item=item)
trip.refresh_from_db()
print('after delete:', trip.computed_budget_total)
"
```

**Rollback strategy:** because `computed_budget_total` is fully recomputable from `BudgetLineItem` rows at any time, if it's ever suspected to have drifted (e.g., due to a bulk operation that bypassed signals, such as `.update()` calls, which famously do **not** trigger signals in Django), the fix is a one-off reconciliation script calling `calculate_budget_total()` for every `Trip` and writing the result back — worth noting explicitly here as the one real gap in this design: **`QuerySet.update()` and `bulk_create()`/`bulk_update()` bypass signals entirely.** Any future bulk operation on `BudgetLineItem` (Chapter 13's AI agent, if it ever bulk-inserts estimated line items) must either avoid bulk methods or manually call the recalculation logic afterward — flagged here so it isn't forgotten three chapters from now.

---

## 14. Testing

### 14.1 `apps/budget/tests/test_models.py`

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.budget.models import BudgetLineItem
from apps.trips.models import Trip

User = get_user_model()


class BudgetLineItemModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="b@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )

    def test_negative_amount_rejected_at_db_level(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BudgetLineItem.objects.create(
                    budget=self.trip.budget, category="food",
                    description="bad", amount=Decimal("-10.00"),
                )
```

### 14.2 `apps/budget/tests/test_signals.py`

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget import services
from apps.budget.models import Budget
from apps.trips.models import Trip

User = get_user_model()


class BudgetAutoCreationSignalTests(TestCase):
    def test_budget_auto_created_with_trip(self):
        user = User.objects.create_user(email="s@example.com", password="pass1234")
        self.assertEqual(Budget.objects.count(), 0)
        Trip.objects.create(user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5))
        self.assertEqual(Budget.objects.count(), 1)


class RecalculateTripBudgetTotalSignalTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="s2@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )

    def test_total_starts_at_zero(self):
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.computed_budget_total, Decimal("0.00"))

    def test_total_updates_on_line_item_creation(self):
        services.add_line_item(
            budget=self.trip.budget, category="food", description="Dinner", amount=Decimal("50.00"),
        )
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.computed_budget_total, Decimal("50.00"))

    def test_total_updates_on_multiple_line_items(self):
        services.add_line_item(budget=self.trip.budget, category="food", description="A", amount=Decimal("50.00"))
        services.add_line_item(budget=self.trip.budget, category="transport", description="B", amount=Decimal("30.00"))
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.computed_budget_total, Decimal("80.00"))

    def test_total_updates_on_line_item_deletion(self):
        item = services.add_line_item(
            budget=self.trip.budget, category="food", description="Dinner", amount=Decimal("50.00"),
        )
        services.delete_line_item(line_item=item)
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.computed_budget_total, Decimal("0.00"))
```

### 14.3 `apps/budget/tests/test_selectors.py`

```python
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.budget import services
from apps.budget.selectors import calculate_budget_total, get_budget_summary
from apps.trips.models import Trip

User = get_user_model()


class BudgetSelectorTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="sel@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=user, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )
        self.budget = self.trip.budget
        self.budget.planned_total = Decimal("100.00")
        self.budget.save()

    def test_calculate_total_on_empty_budget_returns_zero_not_none(self):
        self.assertEqual(calculate_budget_total(budget=self.budget), Decimal("0.00"))

    def test_summary_by_category_breakdown(self):
        services.add_line_item(budget=self.budget, category="food", description="A", amount=Decimal("30.00"))
        services.add_line_item(budget=self.budget, category="food", description="B", amount=Decimal("20.00"))
        services.add_line_item(budget=self.budget, category="transport", description="C", amount=Decimal("15.00"))

        summary = get_budget_summary(budget=self.budget)
        self.assertEqual(summary["actual_total"], Decimal("65.00"))
        self.assertEqual(summary["remaining"], Decimal("35.00"))
        categories = {row["category"]: row["subtotal"] for row in summary["by_category"]}
        self.assertEqual(categories["food"], Decimal("50.00"))
        self.assertEqual(categories["transport"], Decimal("15.00"))

    def test_summary_query_count_is_fixed(self):
        services.add_line_item(budget=self.budget, category="food", description="A", amount=Decimal("30.00"))
        with self.assertNumQueries(2):
            get_budget_summary(budget=self.budget)
```

### 14.4 `apps/budget/tests/test_views.py`

```python
from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.trips.models import Trip

User = get_user_model()


class BudgetAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.stranger = User.objects.create_user(email="stranger@example.com", password="pass1234")
        self.trip = Trip.objects.create(
            user=self.owner, title="Test", start_date=date(2026, 1, 1), end_date=date(2026, 1, 5)
        )
        self.owner_token = self._login("owner@example.com")
        self.stranger_token = self._login("stranger@example.com")

    def _login(self, email):
        response = self.client.post(reverse("accounts:login"), {"email": email, "password": "pass1234"})
        return response.data["tokens"]["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_add_line_item_and_read_summary(self):
        self.client.post(
            reverse("budget:line-items", kwargs={"trip_pk": self.trip.pk}),
            {"category": "food", "description": "Dinner", "amount": "45.00"},
            **self._auth(self.owner_token),
        )
        response = self.client.get(
            reverse("budget:summary", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.owner_token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["actual_total"], "45.00")

    def test_negative_amount_rejected_with_400(self):
        response = self.client.post(
            reverse("budget:line-items", kwargs={"trip_pk": self.trip.pk}),
            {"category": "food", "description": "Bad", "amount": "-10.00"},
            **self._auth(self.owner_token),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stranger_gets_404(self):
        response = self.client.get(
            reverse("budget:detail", kwargs={"trip_pk": self.trip.pk}), **self._auth(self.stranger_token)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_line_item_updates_trip_total(self):
        create_response = self.client.post(
            reverse("budget:line-items", kwargs={"trip_pk": self.trip.pk}),
            {"category": "food", "description": "Dinner", "amount": "45.00"},
            **self._auth(self.owner_token),
        )
        line_item_id = create_response.data["id"]
        self.client.delete(
            reverse("budget:line-item-detail", kwargs={"trip_pk": self.trip.pk, "line_item_pk": line_item_id}),
            **self._auth(self.owner_token),
        )
        self.trip.refresh_from_db()
        self.assertEqual(str(self.trip.computed_budget_total), "0.00")
```

Run everything:

```bash
docker compose exec web python manage.py test apps.budget -v 2
```

---

## 15. Git Commit

```bash
git add apps/budget/
git commit -m "feat(budget): Budget/BudgetLineItem, aggregation, denormalized total sync

- Budget: one-to-one with Trip, auto-created via signal (same
  pattern as Chapter 5's Profile/User)
- BudgetLineItem: many-to-one with Budget (same shape as Chapter 8's
  ItineraryItem/ItineraryDay), CheckConstraint amount >= 0
- calculate_budget_total() uses Coalesce to avoid the None-on-empty
  aggregation trap; explicit output_field to avoid FieldError
- recalculate_trip_budget_total signal fires on BOTH post_save and
  post_delete of BudgetLineItem (post_save alone would leave stale
  totals after deletion) — closes the loop on Architecture Handbook
  ADR-7's denormalized Trip.computed_budget_total
- get_budget_summary(): total + per-category breakdown + planned-vs-
  actual remaining, proven at a FIXED 2 queries via assertNumQueries
- KNOWN GAP documented: QuerySet.update()/bulk_create()/bulk_update()
  bypass signals — flagged for Chapter 13's AI agent to handle
  explicitly when it starts writing line items in bulk

Chapter 9 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Budget.trip` is `OneToOneField(..., CASCADE)`, auto-created via signal
- [ ] `BudgetLineItem.amount` has both a DB `CheckConstraint` and serializer validation rejecting negatives
- [ ] `calculate_budget_total()` returns `Decimal('0.00')`, never `None`, for an empty budget
- [ ] Recalculation signal fires on both `post_save` and `post_delete` — verified by a dedicated deletion test
- [ ] `get_budget_summary()` query count proven fixed via `assertNumQueries`
- [ ] Cross-user access returns 404 (consistent with Chapter 8's itinerary convention)
- [ ] The `QuerySet.update()`/bulk-operation signal gap is documented, not silently left as a landmine
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 10 — `recommendations` App: Suggestion Engine (Data Layer)** closes out Volume 3 by building the `Recommendation` model and its accept/reject workflow — read-mostly, AI-populated data (per Architecture Handbook §4.4: "read-mostly, AI-populated, user can accept/reject"). This chapter builds only the *data layer and API* for recommendations; the AI that actually generates them doesn't arrive until Chapter 15's Recommendation Agent. This is also where we establish the pattern for a model that starts empty and is populated exclusively by a future AI agent — the same "structure first, intelligence later" discipline already applied to itinerary (Chapter 8) and budget (this chapter). Say **"Continue to Chapter 10"** when ready.
