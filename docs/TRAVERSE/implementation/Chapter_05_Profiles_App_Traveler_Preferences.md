# Chapter 5 — `profiles` App: Traveler Preferences

**Volume 2: Identity & Core Domain | Chapter 5 of 29**

> This is the first app in the project with a real foreign key to `User`, and the first to use Django signals. `Profile` holds everything about *how* a person likes to travel — budget style, interests, dietary needs — kept deliberately separate from `accounts` (identity) per Architecture Handbook §4.4. Every AI agent from Chapter 12 onward will eventually read from this model to personalize its output.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Model a one-to-one relationship correctly, including the delete-cascade decision and why it's the right one here.
- Use Django's `choices` pattern properly with `TextChoices` instead of raw string constants scattered through code.
- Write a `post_save` signal that auto-creates a `Profile` the instant a `User` registers, and explain why signal logic must stay thin.
- Build a self-serve "get/update my profile" API that never lets a user access anyone else's profile, without needing a URL parameter for the profile ID at all.

---

## 2. Theory

### 2.1 Why `Profile` Is Not Just More Fields On `User` (ELI10)

Imagine `User` as your passport — it proves who you are and rarely changes. `Profile` is more like your travel diary of preferences — how much you like to spend, what kind of food you enjoy, whether you travel with kids. These change more often, are queried differently (an AI agent wants "give me this user's preferences," never "give me this user's password hash"), and conceptually belong to a different part of the system. Splitting them keeps `accounts` focused purely on identity/security and keeps `profiles` focused purely on personalization — this is the Single Responsibility Principle applied at the model level, not just the class level.

### 2.2 What a Signal Is (ELI10)

A Django signal is like a bell that rings automatically whenever something happens — in this case, "a new `User` was just saved." Other code can "listen" for that bell and react, without the `User` model itself needing to know anything about `Profile`. This keeps `accounts` (Chapter 4) completely unaware that `profiles` even exists — the dependency only flows one direction, from `profiles` toward `accounts`, never the reverse. This matches the app dependency graph from Architecture Handbook §4.3 exactly.

### 2.3 Why Signal Logic Must Stay Thin

Signals run automatically, invisibly, as a side effect of something else. If a signal handler contains complex business logic and something breaks, the traceback appears to come from `User.save()` — a completely unrelated-looking place — which is confusing to debug. The rule enforced starting here, project-wide: **a signal handler does one obvious thing and calls out to a real function (often in `services.py`) for anything more complex than that.**

---

## 3. Architecture Decision

**Decision:** `Profile.user` is a `OneToOneField` with `on_delete=CASCADE`, auto-created via a `post_save` signal on `User` with `created=True`.

**Alternative considered:** Create the `Profile` lazily, the first time a user visits their profile page, using `get_or_create`. **Rejected because:** this means `Profile` might not exist yet when Chapter 12's AI agents look it up, forcing every future consumer of `Profile` to handle a "does not exist yet" branch. Auto-creating it at registration time guarantees **every** `User` has **exactly one** `Profile`, always, which every future app can then rely on as an invariant rather than a maybe.

**Decision:** Preference fields (`budget_style`, `travel_pace`, `dietary_restrictions`) use Django's `TextChoices` pattern, not free-text fields.

**Trade-off documented:** choices are less flexible than free text (a user can't type "moderately-frugal-but-splurges-on-food") — accepted because Chapter 9's Budget Agent and Chapter 15's Recommendation Agent need **predictable, enumerable** values to reason over reliably; free text would require the AI to interpret arbitrary phrasing every single time, which is slower, more expensive, and less reliable than a closed set of options.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Profile` model | Needs `User` (Chapter 4) to already exist to have something to point a `OneToOneField` at |
| Write the signal | Needs `Profile` to exist first — the signal creates instances of it |
| Register the signal in `apps.py`'s `ready()` | Django will not call signal handlers that are merely *defined* but never *connected* — this step is easy to forget and silently does nothing if skipped |
| Build the API | Needs the model and signal both working, so "my profile always exists" is a safe assumption in the view code |
| Write tests proving auto-creation | Must exist before Chapter 6 onward starts *relying* on this invariant elsewhere |

---

## 5. File Structure

```
apps/profiles/
├── __init__.py
├── apps.py                # gains a ready() method this chapter
├── models.py               # Profile, TextChoices enums
├── signals.py               # create_profile_on_user_creation
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
    └── test_views.py
```

---

## 6. Folder Location

All new files under `apps/profiles/`. One existing file is touched: `apps/profiles/apps.py` (adding `ready()`).

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations profiles
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test apps.profiles
```

---

## 8. Docker Commands

```bash
docker compose restart web   # required — signal registration happens at app load time
```

**Why a restart is non-negotiable here, more so than usual:** signal connections happen once, when `AppConfig.ready()` runs at process boot. If you edit `signals.py` while Gunicorn is still running the old process, the new signal handler is simply never connected — this produces the confusing symptom of "I added the signal but profiles still aren't being created," which is actually just a stale process, not a code bug.

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations profiles
Migrations for 'profiles':
  apps/profiles/migrations/0001_initial.py
    - Create model Profile

$ docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.create_user(email='sig@example.com', password='pass1234')
print(hasattr(u, 'profile'), u.profile.budget_style)
"
True moderate
```

---

## 10. Code

### 10.1 `apps/profiles/models.py`

```python
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class BudgetStyle(models.TextChoices):
    SHOESTRING = "shoestring", "Shoestring / Backpacker"
    MODERATE = "moderate", "Moderate"
    COMFORT = "comfort", "Comfort"
    LUXURY = "luxury", "Luxury"


class TravelPace(models.TextChoices):
    RELAXED = "relaxed", "Relaxed — few activities per day"
    BALANCED = "balanced", "Balanced"
    PACKED = "packed", "Packed — see as much as possible"


class DietaryRestriction(models.TextChoices):
    NONE = "none", "No restrictions"
    VEGETARIAN = "vegetarian", "Vegetarian"
    VEGAN = "vegan", "Vegan"
    HALAL = "halal", "Halal"
    KOSHER = "kosher", "Kosher"
    GLUTEN_FREE = "gluten_free", "Gluten-Free"


class Profile(TimeStampedModel):
    """
    One-to-one traveler preference profile. Always exists for every
    User — auto-created via signal, never created manually through
    normal application flow (see signals.py).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    budget_style = models.CharField(
        max_length=20, choices=BudgetStyle.choices, default=BudgetStyle.MODERATE,
    )
    travel_pace = models.CharField(
        max_length=20, choices=TravelPace.choices, default=TravelPace.BALANCED,
    )
    dietary_restrictions = models.CharField(
        max_length=20, choices=DietaryRestriction.choices, default=DietaryRestriction.NONE,
    )
    interests = models.JSONField(
        default=list, blank=True,
        help_text="List of free-form interest tags, e.g. ['hiking', 'museums', 'nightlife'].",
    )
    home_country = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self) -> str:
        return f"Profile<{self.user.email}>"
```

**Why `interests` is a `JSONField` list, not a `choices` field like the others:** interests are open-ended and expected to grow (Architecture Handbook §13 anticipates "personalized ranking model" — a fixed, closed set of interest choices would need constant migration edits as new interests are discovered). `budget_style`/`travel_pace`/`dietary_restrictions`, by contrast, are genuinely closed, small, stable sets, so `TextChoices` is the right tool for those specifically — the two patterns are chosen field-by-field, not uniformly.

### 10.2 `apps/profiles/signals.py`

```python
"""
Signal handlers for the profiles app. Kept intentionally thin —
the handler itself does exactly one thing (create a Profile) and
delegates nothing further, per Chapter 5 Theory §2.3.
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.profiles.models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
```

**Why `sender=settings.AUTH_USER_MODEL` (a string) instead of importing `User` directly:** importing `apps.accounts.models.User` directly into `apps.profiles.signals` would work, but using the settings string keeps `profiles` from ever needing a hard import of `accounts`'s model class — a small extra layer of decoupling that pays off if the user model's import path ever needs to change (unlikely per Chapter 4, but the pattern itself is good practice regardless).

**Why `if created:` matters:** `post_save` fires on *every* save, not just creation — an update to an existing `User` (e.g., changing their name) would otherwise try to create a duplicate `Profile` and crash on the `OneToOneField` uniqueness constraint. `created` is a boolean Django provides specifically to distinguish these two cases.

### 10.3 `apps/profiles/apps.py`

```python
from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    verbose_name = "Traveler Profiles"

    def ready(self):
        import apps.profiles.signals  # noqa: F401  — registers the receiver
```

**Why the import happens inside `ready()`, not at the top of the file:** importing `signals.py` at module import time (before Django's app registry is fully populated) risks `AppRegistryNotReady` errors, since `signals.py` imports the `Profile` model. `ready()` is the framework-provided hook guaranteed to run only after all apps are loaded — this is a Django convention, not a project-specific choice.

### 10.4 `apps/profiles/serializers.py`

```python
from rest_framework import serializers

from apps.profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id", "budget_style", "travel_pace", "dietary_restrictions",
            "interests", "home_country", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_interests(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("interests must be a list of strings.")
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("every interest must be a string.")
        if len(value) > 20:
            raise serializers.ValidationError("a maximum of 20 interests is supported.")
        return [item.strip().lower() for item in value if item.strip()]
```

### 10.5 `apps/profiles/views.py`

```python
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from apps.profiles.serializers import ProfileSerializer


class MyProfileView(RetrieveUpdateAPIView):
    """
    Self-serve profile endpoint. Deliberately takes NO id/pk in the
    URL at all — the profile acted on is always request.user's own,
    which structurally makes it impossible to view or edit someone
    else's profile through this endpoint (no ownership check needed
    because there is no other object reachable in the first place).
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
```

**Why no `pk` in the URL, and no `IsOwner` permission needed here:** Chapter 3's `IsOwner` permission is for objects reached by ID in a URL (like `Trip` from Chapter 7). Here, we sidestep that whole problem category by design — `get_object()` always resolves to `request.user.profile`, so there is no ID a malicious user could substitute in the first place. This is a stronger guarantee than an owner-check on an ID-based endpoint: a missing permission check can be forgotten, but a URL with no ID parameter has nothing to attack.

### 10.6 `apps/profiles/urls.py`

```python
from django.urls import path

from apps.profiles.views import MyProfileView

app_name = "profiles"

urlpatterns = [
    path("me/", MyProfileView.as_view(), name="my-profile"),
]
```

### 10.7 `config/urls.py` (addition)

```python
path("api/v1/profile/", include("apps.profiles.urls")),
```

### 10.8 `apps/profiles/admin.py`

```python
from django.contrib import admin

from apps.profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "budget_style", "travel_pace", "dietary_restrictions", "created_at"]
    list_filter = ["budget_style", "travel_pace", "dietary_restrictions"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["user"]
```

**Note:** `autocomplete_fields = ["user"]` requires `UserAdmin` (Chapter 4) to declare `search_fields`, which it already does — Django admin autocomplete widgets depend on the *related* model's admin having search fields configured, another small cross-app dependency worth knowing about.

---

## 11. Code Walkthrough

- **`related_name="profile"` (singular) on the `OneToOneField`**: this is what makes `user.profile` valid Python — Django uses `related_name` to name the reverse accessor. Getting this right is what lets `MyProfileView.get_object()` simply return `self.request.user.profile` with no query logic of its own.
- **The signal is tested independently of the view (Section 14)**: this proves the *auto-creation invariant* holds regardless of *how* a `User` gets created — via the API, via `createsuperuser`, via a data migration, via a test factory — anywhere `User.objects.create_user()` (or `.create()`) is called, the signal fires the same way.
- **`ProfileSerializer.validate_interests` normalizes casing and whitespace**: this is a small but important detail — without it, `"Hiking"` and `"hiking"` would be treated as different interests by any future AI agent or analytics grouping, silently fragmenting what should be the same tag.
- **No `create` method on the serializer**: `Profile` is never created through this serializer — only ever read and updated, because creation is exclusively the signal's job. This is enforced by the view only ever calling `get_object()` (never `perform_create`), not by anything in the serializer itself — worth knowing as an implicit contract between these two files.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `RelatedObjectDoesNotExist: User has no profile` | Signal not connected (forgot `ready()`, or process wasn't restarted after adding it) | Confirm `apps.py.ready()` imports `signals`, then `docker compose restart web` |
| `IntegrityError: UNIQUE constraint failed: profiles_profile.user_id` | Something tried to create a second `Profile` for the same user | Check for any code path calling `Profile.objects.create()` directly instead of relying on the signal |
| Profile appears empty/default even after a user "updated" it during registration | Confusing registration-time defaults with an actual profile update — `RegisterSerializer` (Chapter 4) never touches `Profile` at all, by design | This is expected; the user must call `PATCH /api/v1/profile/me/` separately after registering |
| `AppRegistryNotReady` on boot | `import apps.profiles.signals` was placed at the top of `apps.py` instead of inside `ready()` | Move the import inside `ready()` exactly as shown in 10.3 |

---

## 13. Debugging

```bash
# 1. Confirm the signal is actually connected
docker compose exec web python manage.py shell -c "
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
receivers = post_save._live_receivers(sender=get_user_model())
print([r.__name__ for r in receivers])
"
# Expected output includes: create_profile_on_user_creation

# 2. Confirm every existing user actually has a profile (useful after any
#    signal-related bugfix, to check for orphaned users from before the fix)
docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
orphans = User.objects.filter(profile__isnull=True)
print(f'Users without a profile: {orphans.count()}')
"
```

**Rollback strategy:** if the signal is found to have a bug after some users were already created without a profile (the `orphans` query above), the fix is a one-off data-repair management command (`python manage.py backfill_profiles`), not a schema rollback — this is a good moment to note that **signals fix future data, not past data**, and any signal bug discovered late always needs a matching backfill step.

---

## 14. Testing

### 14.1 `apps/profiles/tests/test_models.py`

```python
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models import BudgetStyle, DietaryRestriction, Profile, TravelPace

User = get_user_model()


class ProfileModelTests(TestCase):
    def test_str_representation(self):
        user = User.objects.create_user(email="a@example.com", password="pass1234")
        self.assertEqual(str(user.profile), "Profile<a@example.com>")

    def test_defaults(self):
        user = User.objects.create_user(email="b@example.com", password="pass1234")
        profile = user.profile
        self.assertEqual(profile.budget_style, BudgetStyle.MODERATE)
        self.assertEqual(profile.travel_pace, TravelPace.BALANCED)
        self.assertEqual(profile.dietary_restrictions, DietaryRestriction.NONE)
        self.assertEqual(profile.interests, [])

    def test_one_to_one_prevents_duplicate_profile(self):
        user = User.objects.create_user(email="c@example.com", password="pass1234")
        with self.assertRaises(Exception):
            Profile.objects.create(user=user)

    def test_cascade_delete(self):
        user = User.objects.create_user(email="d@example.com", password="pass1234")
        profile_id = user.profile.id
        user.delete()
        self.assertFalse(Profile.objects.filter(id=profile_id).exists())
```

### 14.2 `apps/profiles/tests/test_signals.py`

```python
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models import Profile

User = get_user_model()


class ProfileSignalTests(TestCase):
    def test_profile_auto_created_on_user_creation(self):
        self.assertEqual(Profile.objects.count(), 0)
        User.objects.create_user(email="new@example.com", password="pass1234")
        self.assertEqual(Profile.objects.count(), 1)

    def test_profile_not_duplicated_on_user_resave(self):
        user = User.objects.create_user(email="resave@example.com", password="pass1234")
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
        user.first_name = "Changed"
        user.save()
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

    def test_superuser_creation_also_creates_profile(self):
        user = User.objects.create_superuser(email="admin@example.com", password="pass1234")
        self.assertTrue(hasattr(user, "profile"))
```

### 14.3 `apps/profiles/tests/test_views.py`

```python
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class MyProfileViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="p@example.com", password="pass1234")
        login = self.client.post(
            reverse("accounts:login"), {"email": "p@example.com", "password": "pass1234"}
        )
        self.access = login.data["tokens"]["access"]

    def _auth(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.access}"}

    def test_requires_authentication(self):
        response = self.client.get(reverse("profiles:my-profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_own_profile(self):
        response = self.client.get(reverse("profiles:my-profile"), **self._auth())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["budget_style"], "moderate")

    def test_patch_updates_own_profile(self):
        response = self.client.patch(
            reverse("profiles:my-profile"),
            {"budget_style": "luxury", "interests": ["Museums", " hiking "]},
            **self._auth(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["budget_style"], "luxury")
        self.assertEqual(response.data["interests"], ["museums", "hiking"])

    def test_patch_invalid_budget_style_rejected(self):
        response = self.client.patch(
            reverse("profiles:my-profile"), {"budget_style": "not_a_real_choice"}, **self._auth()
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_interests_over_limit_rejected(self):
        response = self.client.patch(
            reverse("profiles:my-profile"),
            {"interests": [f"tag{i}" for i in range(25)]},
            **self._auth(),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.profiles -v 2
```

---

## 15. Git Commit

```bash
git add apps/profiles/ config/urls.py
git commit -m "feat(profiles): Profile model, auto-creation signal, self-serve API

- Profile: one-to-one with User, CASCADE delete
- BudgetStyle/TravelPace/DietaryRestriction as TextChoices;
  interests as an open JSONField list (deliberately not choices —
  see Chapter 5 for why the split)
- post_save signal on User auto-creates Profile (created=True guard),
  registered via ProfilesConfig.ready()
- MyProfileView: no pk in URL, get_object() always resolves to
  request.user.profile — no IsOwner check needed by construction
- Full coverage: model constraints, signal behavior (incl. no
  duplication on re-save, superuser path), API auth/validation

Every User now structurally guaranteed to have exactly one Profile.

Chapter 5 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Profile.user` is `OneToOneField(..., on_delete=CASCADE)`
- [ ] `BudgetStyle`, `TravelPace`, `DietaryRestriction` implemented as `TextChoices`
- [ ] `interests` implemented as a validated `JSONField` list, not `TextChoices`
- [ ] `post_save` signal created, thin, guarded by `if created:`
- [ ] Signal registered via `ProfilesConfig.ready()`, not at module import time
- [ ] `docker compose restart web` performed after adding the signal
- [ ] `MyProfileView` takes no `pk`/`id` URL parameter
- [ ] Every test passing, including the "no duplication on re-save" signal test
- [ ] Manually verified: registering a new user via Chapter 4's `/register/` immediately produces a working `/api/v1/profile/me/` response
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 6 — `destinations` App: Reference Catalog** introduces the project's first model that has **no** foreign key to `User` at all — reference data shared by everyone. This chapter covers seed data via a management command (not a signal, since there's no per-user trigger), search/filtering on the API, and why reference-data endpoints get `IsStaffOrReadOnly` (built back in Chapter 3) instead of `IsAuthenticated` alone. Say **"Continue to Chapter 6"** when ready.
