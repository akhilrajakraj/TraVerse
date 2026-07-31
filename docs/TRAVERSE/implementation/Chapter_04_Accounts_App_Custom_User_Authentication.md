# Chapter 4 — `accounts` App: Custom User & Authentication

**Volume 2: Identity & Core Domain | Chapter 4 of 29**

> This is the highest-stakes chapter in the entire build so far. Django allows you to swap the user model exactly once: before the very first migration is ever applied to the database. Get this wrong, and the fix later is a painful, risky data migration — not a quick edit. Everything from Chapter 5 onward (`Profile`, `Trip`, `ChatSession`, `AgentRun`...) has a foreign key back to whatever we define here.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Explain why Django requires a custom user model to be declared before the first migration, and what breaks if you try to add one later.
- Build an email-based custom `User` model (no `username` field) with a correct custom manager.
- Wire JWT authentication end-to-end using SimpleJWT: register, login (token pair), refresh, logout (blacklist).
- Build a global DRF exception handler that turns Chapter 3's `ApplicationError` hierarchy into consistent, predictable API responses.
- Prove the entire auth flow works with real HTTP requests, not just unit tests in isolation.

---

## 2. Theory

### 2.1 Why Django Only Lets You Swap the User Model Once (ELI10)

Every single table Django's built-in apps create — `admin` log entries, permissions, sessions — has a foreign key pointing at "the user model." The very first migration that runs for `django.contrib.auth` bakes in *which* table that foreign key points to. If you change your mind after that migration has run against a real database, you'd need to rewrite every foreign key in every table that ever pointed at the old user table — this is why the *entire industry* treats "use a custom user model from day one" as a hard rule, not a nice-to-have. We're doing it in Chapter 4, before Chapter 5's `Profile` or Chapter 7's `Trip` create a single foreign key to `User`, and — critically — before we've run **any** migration at all, including Django's own built-in ones.

### 2.2 Why Email Instead Of Username

Nobody remembers a travel-planning app username. Everybody remembers their email. Using email as the unique login identifier removes an entire category of "forgot my username" support tickets and matches how virtually every modern SaaS product actually authenticates users.

### 2.3 Why JWT Instead Of Django Sessions

Architecture Handbook ADR-6 already made this call: JWT enables a fully decoupled frontend (SPA, mobile app) without cookie/CSRF cross-domain complications. This chapter is where that decision becomes real code.

### 2.4 What JWT Actually Is (ELI10)

A JWT is like a wristband at a concert. Security scans your ticket once at the door (login), then staples on a wristband (the token) that proves you were checked, without needing to re-check your ticket every single time you walk past a different stage. The wristband has an expiry — eventually you need a new one (refresh token), or you have to leave and re-enter (log in again).

---

## 3. Architecture Decision

**Decision:** `User` extends `AbstractBaseUser` + `PermissionsMixin` (not `AbstractUser`), with `email` as `USERNAME_FIELD`, no `username` field at all, and a custom `UserManager`.

**Alternative considered:** Extend `AbstractUser` and just make `email` unique, keeping `username` around unused. **Rejected because:** an unused-but-present `username` field is a real footgun — someone will eventually write code against it, or a form will silently require it, out of habit. Removing it entirely makes the "email is the only identifier" rule structurally enforced, not just documented.

**Decision:** JWT via `djangorestframework-simplejwt`, with access tokens short-lived (15 minutes) and refresh tokens longer-lived (7 days) with rotation and blacklisting enabled.

**Trade-off documented:** rotation + blacklisting requires an extra database table (`OutstandingToken`/`BlacklistedToken`, provided by the package) and a few extra queries per refresh — accepted in exchange for the ability to actually revoke a stolen refresh token, which a plain non-rotating JWT setup cannot do.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Write `User` model | Must exist before `AUTH_USER_MODEL` is set |
| Set `AUTH_USER_MODEL` in settings | Must happen before the FIRST `makemigrations`/`migrate` ever runs |
| Run initial migrations | Only after both of the above — this is the point of no return for the user model choice |
| Register in admin | Needs the migrated table to exist |
| Build serializers/views for register/login | Needs the model to exist first |
| Build the global exception handler | Needed now because login/register are the first views that can realistically raise `ApplicationError` subclasses from Chapter 3 |

---

## 5. File Structure

```
apps/accounts/
├── __init__.py
├── apps.py
├── models.py                # User, UserManager
├── managers.py               # (kept separate from models.py per project convention)
├── admin.py
├── serializers.py            # RegisterSerializer, LoginSerializer, UserSerializer
├── permissions.py            # (empty for now — accounts has no ownership-style objects yet)
├── exceptions.py              # Account-specific exceptions extending core.exceptions
├── urls.py
├── views.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_serializers.py
    └── test_views.py

config/
├── settings/base.py           # AUTH_USER_MODEL, SIMPLE_JWT config, REST_FRAMEWORK config
└── exception_handler.py        # NEW — global DRF exception handler, project-wide, not accounts-specific
```

**Why `exception_handler.py` lives in `config/`, not `apps/accounts/`:** it's not an accounts concern — it's a project-wide concern that happens to be *implemented* here because this is the first chapter with real views to prove it against. Every future app's views benefit from it automatically once wired into `REST_FRAMEWORK` settings.

---

## 6. Folder Location

All commands run from `project-root/`. New files land in `apps/accounts/` and `config/`.

---

## 7. Terminal Commands

```bash
# Install SimpleJWT if not already a DockForge base dependency (check requirements/base.txt first)
docker compose exec web pip show djangorestframework-simplejwt

# Generate the FIRST migration of the entire project — this is the point of no return
docker compose exec web python manage.py makemigrations accounts

# Apply it
docker compose exec web python manage.py migrate

# Create a superuser to manually verify the admin site
docker compose exec web python manage.py createsuperuser
```

**Why `makemigrations accounts` is run before any other app's migrations, even `core`'s:** `core` has no concrete models (Chapter 3), so it produces no migration at all. `accounts` is therefore the true first migration of the project — this is the exact moment `AUTH_USER_MODEL` gets locked in.

---

## 8. Docker Commands

```bash
docker compose exec web python manage.py test apps.accounts
docker compose restart web   # required after AUTH_USER_MODEL / SIMPLE_JWT settings changes
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py makemigrations accounts
Migrations for 'accounts':
  apps/accounts/migrations/0001_initial.py
    - Create model User

$ docker compose exec web python manage.py migrate
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, sessions, token_blacklist
Running migrations:
  Applying accounts.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying token_blacklist.0001_initial... OK
```

Note that `accounts.0001_initial` applies **first**, before `admin` — this ordering is Django automatically resolving the dependency correctly once `AUTH_USER_MODEL` points at it; if you ever see `admin` or `auth` apply before `accounts`, stop and check your settings immediately.

---

## 10. Code

### 10.1 `apps/accounts/managers.py`

```python
"""
Custom manager for the email-based User model.
Required because Django's default UserManager assumes a `username`
field exists, which our User model deliberately does not have.
"""
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
```

### 10.2 `apps/accounts/models.py`

```python
"""
Custom User model. This is the ONLY user model this project will
ever have — see Chapter 4 Theory (§2.1) for why it cannot be
meaningfully swapped later.
"""
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import TimeStampedModel


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Email-authenticated user. Deliberately has NO username field.

    Inherits created_at/updated_at from TimeStampedModel (Chapter 3).
    Inherits is_staff/is_superuser/groups/permissions from
    PermissionsMixin (Django built-in — reused, not reinvented).
    """
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are already required by Django internals

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self) -> str:
        return self.first_name or self.email
```

**Why `TimeStampedModel` is inherited here despite `User` being unusually foundational:** every other model in the project gets `created_at`/`updated_at` for free — there's no principled reason `User` should be the one exception, and "when did this account get created" is a genuinely useful, commonly-needed field (support debugging, analytics in Chapter 24).

### 10.3 `config/settings/base.py` (additions)

```python
# --- Custom user model — MUST be set before the first migrate ever runs ---
AUTH_USER_MODEL = "accounts.User"

# --- REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "config.exception_handler.application_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# --- SimpleJWT ---
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Add to THIRD_PARTY_APPS from Chapter 2:
# "rest_framework_simplejwt.token_blacklist",
```

**Why access tokens are only 15 minutes:** a stolen access token is only useful to an attacker for 15 minutes, minimizing blast radius, while the longer-lived refresh token is protected by rotation + blacklisting — the standard defense-in-depth pattern for JWT systems.

### 10.4 `apps/accounts/exceptions.py`

```python
from apps.core.exceptions import ApplicationError


class EmailAlreadyRegistered(ApplicationError):
    default_message = "An account with this email already exists."
    default_code = "email_already_registered"


class InvalidCredentials(ApplicationError):
    default_message = "Email or password is incorrect."
    default_code = "invalid_credentials"
```

### 10.5 `config/exception_handler.py`

```python
"""
Global DRF exception handler. Translates our ApplicationError
hierarchy (Chapter 3) into consistent JSON error responses, while
still letting DRF's default handler deal with its own exception
types (ValidationError, NotAuthenticated, etc.) unchanged.
"""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from apps.core.exceptions import (
    ApplicationError,
    ExternalServiceError,
    ResourceNotOwned,
)

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    ResourceNotOwned: status.HTTP_403_FORBIDDEN,
    ExternalServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
}
_DEFAULT_APPLICATION_ERROR_STATUS = status.HTTP_400_BAD_REQUEST


def application_exception_handler(exc, context):
    if isinstance(exc, ApplicationError):
        http_status = _STATUS_MAP.get(type(exc), _DEFAULT_APPLICATION_ERROR_STATUS)
        logger.warning(
            "ApplicationError handled: code=%s message=%s view=%s",
            exc.code,
            exc.message,
            context.get("view"),
        )
        return Response(
            {"error": {"code": exc.code, "message": exc.message}},
            status=http_status,
        )

    # Fall back to DRF's default handling for everything else
    # (ValidationError, NotAuthenticated, PermissionDenied, etc.)
    return drf_default_handler(exc, context)
```

### 10.6 `apps/accounts/serializers.py`

```python
from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.accounts.exceptions import EmailAlreadyRegistered, InvalidCredentials
from apps.accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name"]
        read_only_fields = ["id"]

    def validate_email(self, value: str) -> str:
        normalized = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized).exists():
            raise EmailAlreadyRegistered()
        return normalized

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        user = authenticate(
            username=attrs["email"], password=attrs["password"]
        )
        if user is None or not user.is_active:
            raise InvalidCredentials()
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "created_at"]
        read_only_fields = fields
```

**Why `authenticate(username=..., password=...)` even though our field is `email`:** Django's `authenticate()` function always passes the login identifier as the `username` kwarg internally, regardless of what `USERNAME_FIELD` is set to on the model — this is a Django framework quirk, not an inconsistency in our own code, and is worth calling out explicitly since it trips up almost everyone the first time.

### 10.7 `apps/accounts/views.py`

```python
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken as RT

from apps.accounts.serializers import LoginSerializer, RegisterSerializer, UserSerializer


def _tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _tokens_for_user(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": _tokens_for_user(user),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": {"code": "refresh_required", "message": "refresh token is required"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RT(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"error": {"code": "invalid_token", "message": "refresh token is invalid or already blacklisted"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
```

### 10.8 `apps/accounts/urls.py`

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, LogoutView, MeView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
```

### 10.9 `config/urls.py` (addition)

```python
from django.urls import include, path

urlpatterns = [
    # ... existing DockForge-provided paths (admin, health) untouched ...
    path("api/v1/auth/", include("apps.accounts.urls")),
]
```

### 10.10 `apps/accounts/admin.py`

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-created_at"]
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active", "created_at"]
    list_filter = ["is_staff", "is_active", "created_at"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
```

---

## 11. Code Walkthrough

- **`UserManager.use_in_migrations = True`**: without this, Django won't serialize the manager into migration files, which can cause subtle issues with `createsuperuser` during fresh database setups in CI (Chapter 28) — a small flag that avoids a real, hard-to-diagnose class of bug.
- **`RegisterSerializer.validate_email` uses `email__iexact`**: prevents `User@Example.com` and `user@example.com` from being treated as two different accounts — a common real-world bug in email-based auth systems.
- **`_tokens_for_user` is a module-level function, not duplicated in both `RegisterView` and `LoginView`**: small, but this is the DRY principle in action at the smallest possible scale — two call sites, one implementation.
- **`LogoutView` requires the client to send the refresh token in the body, not just rely on the access token in the header**: this is because *blacklisting* operates on refresh tokens (access tokens are stateless and can't be individually revoked before they naturally expire in 15 minutes) — this is inherent to how JWT works, not a limitation of our implementation.
- **The global exception handler falls back to DRF's default handler for anything that isn't `ApplicationError`**: this means `serializer.is_valid(raise_exception=True)` (a normal DRF `ValidationError`) still works exactly as DRF users expect — we're *augmenting* DRF's error handling, not replacing it wholesale.

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model 'accounts.User' that has not been installed` | `apps.accounts` not in `INSTALLED_APPS`, or migration order issue | Confirm Chapter 2's `INSTALLED_APPS` entry, re-check `AUTH_USER_MODEL` string matches `app_label.ModelName` |
| `You are trying to add a non-nullable field... to user without a default` during a LATER migration | Someone tried to change `User` after other tables already reference it | This is the exact scenario Section 2.1 warns about — proceed carefully with a proper data migration, never just "make it work" |
| `TypeError: create_user() missing 1 required positional argument: 'email'` from `createsuperuser` | Django's built-in `createsuperuser` command still expects `USERNAME_FIELD` wiring to be correct | Confirm `USERNAME_FIELD = "email"` and `REQUIRED_FIELDS = []` exactly as written |
| `401 Unauthorized` even with a seemingly valid token | Client sending `Authorization: Token <jwt>` instead of `Authorization: Bearer <jwt>` | SimpleJWT requires the `Bearer` scheme — confirm `AUTH_HEADER_TYPES` and client header format |
| `rest_framework_simplejwt.token_blacklist` table missing | Forgot to add it to `INSTALLED_APPS` before migrating | Add it, then `makemigrations`/`migrate` again |

---

## 13. Debugging

```bash
# 1. Confirm which model AUTH_USER_MODEL actually resolves to at runtime
docker compose exec web python manage.py shell -c \
  "from django.contrib.auth import get_user_model; print(get_user_model())"
# Expected: <class 'apps.accounts.models.User'>

# 2. Manually create a user and inspect it
docker compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u = U.objects.create_user(email='debug@example.com', password='testpass123')
print(u.pk, u.email, u.check_password('testpass123'))
"

# 3. Manually decode a JWT to confirm claims (no external tool needed)
docker compose exec web python manage.py shell -c "
from rest_framework_simplejwt.tokens import AccessToken
# paste a real token string here when debugging a specific failure
"
```

**Rollback strategy:** if the `User` model needs a structural change *before* any real user data exists (i.e., still in early development), the safe rollback is: `docker compose exec web python manage.py migrate accounts zero`, delete the migration file, fix the model, regenerate. **This is only safe before real signups exist** — once any production user data exists, this becomes a proper data migration exercise instead, exactly the expensive scenario Section 2.1 was warning about.

---

## 14. Testing

### 14.1 `apps/accounts/tests/test_models.py`

```python
from django.test import TestCase

from apps.accounts.models import User


class UserModelTests(TestCase):
    def test_create_user_sets_hashed_password(self):
        user = User.objects.create_user(email="a@example.com", password="pass1234")
        self.assertNotEqual(user.password, "pass1234")
        self.assertTrue(user.check_password("pass1234"))

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass1234")

    def test_create_superuser_sets_flags(self):
        user = User.objects.create_superuser(email="admin@example.com", password="pass1234")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_str_returns_email(self):
        user = User.objects.create_user(email="a@example.com", password="pass1234")
        self.assertEqual(str(user), "a@example.com")

    def test_get_full_name_falls_back_to_email(self):
        user = User.objects.create_user(email="a@example.com", password="pass1234")
        self.assertEqual(user.get_full_name(), "a@example.com")
```

### 14.2 `apps/accounts/tests/test_views.py`

```python
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class RegisterViewTests(APITestCase):
    def test_register_creates_user_and_returns_tokens(self):
        url = reverse("accounts:register")
        response = self.client.post(url, {
            "email": "new@example.com",
            "password": "strongpass123",
            "first_name": "Ada",
            "last_name": "Lovelace",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_duplicate_email_returns_400_with_correct_code(self):
        User.objects.create_user(email="dup@example.com", password="pass1234")
        url = reverse("accounts:register")
        response = self.client.post(url, {"email": "dup@example.com", "password": "pass1234"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_rejected(self):
        url = reverse("accounts:register")
        response = self.client.post(url, {"email": "short@example.com", "password": "123"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="login@example.com", password="correctpass1")

    def test_login_with_correct_credentials_returns_tokens(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "login@example.com", "password": "correctpass1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["tokens"])

    def test_login_with_wrong_password_returns_400(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "login@example.com", "password": "wrongpass"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "invalid_credentials")


class MeViewTests(APITestCase):
    def test_me_requires_authentication(self):
        url = reverse("accounts:me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_when_authenticated(self):
        user = User.objects.create_user(email="me@example.com", password="pass1234")
        login_response = self.client.post(
            reverse("accounts:login"), {"email": "me@example.com", "password": "pass1234"}
        )
        access = login_response.data["tokens"]["access"]
        response = self.client.get(
            reverse("accounts:me"), HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")


class LogoutViewTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        User.objects.create_user(email="logout@example.com", password="pass1234")
        login_response = self.client.post(
            reverse("accounts:login"), {"email": "logout@example.com", "password": "pass1234"}
        )
        tokens = login_response.data["tokens"]
        response = self.client.post(
            reverse("accounts:logout"),
            {"refresh": tokens["refresh"]},
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Using the same refresh token again must now fail
        refresh_response = self.client.post(
            reverse("accounts:refresh"), {"refresh": tokens["refresh"]}
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
```

Run everything:

```bash
docker compose exec web python manage.py test apps.accounts -v 2
```

---

## 15. Git Commit

```bash
git add apps/accounts/ config/
git commit -m "feat(accounts): custom email-based User model + JWT authentication

- Custom User (AbstractBaseUser + PermissionsMixin), email as
  USERNAME_FIELD, no username field. AUTH_USER_MODEL set BEFORE
  first migration — see Chapter 4 for why this is irreversible
  after the fact.
- UserManager with create_user/create_superuser
- JWT via SimpleJWT: 15min access / 7day rotating+blacklisted refresh
- Global DRF exception handler wiring core.exceptions.ApplicationError
  into consistent {error: {code, message}} responses
- register/login/refresh/logout/me endpoints under /api/v1/auth/
- Admin registered with UserAdmin
- Full test coverage: models, serializers (via views), views

First migration of the entire project (accounts.0001_initial).

Chapter 4 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `User` model has no `username` field, `email` is `USERNAME_FIELD`
- [ ] `AUTH_USER_MODEL = "accounts.User"` set before `accounts.0001_initial` was generated
- [ ] `accounts.0001_initial` applied before `admin`/`auth` migrations (confirmed in migrate output)
- [ ] `createsuperuser` works and superuser can log into `/admin/`
- [ ] Global exception handler wired via `REST_FRAMEWORK["EXCEPTION_HANDLER"]`
- [ ] `/api/v1/auth/register/`, `/login/`, `/refresh/`, `/logout/`, `/me/` all manually verified with `curl` or Postman, not just unit tests
- [ ] Duplicate email registration returns `400` with `code: "email_already_registered"`
- [ ] Wrong password returns `400` with `code: "invalid_credentials"`
- [ ] Logout actually blacklists the refresh token (verified by the test that re-uses it and expects failure)
- [ ] All accounts tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 5 — `profiles` App: Traveler Preferences** builds the first model with a real foreign key to `User`: a one-to-one `Profile`, auto-created via a `post_save` signal the moment a `User` registers. This is also where the project's first `signals.py` file is introduced, along with the pattern for keeping signal logic thin and testable rather than a tangle of side effects. Say **"Continue to Chapter 5"** when ready.
