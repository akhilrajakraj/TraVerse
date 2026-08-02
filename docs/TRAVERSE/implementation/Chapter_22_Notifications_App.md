# Chapter 22 — `notifications` App

**Volume 6: Supporting Apps | Chapter 22 of 29**

> The project's first genuinely one-way, fire-and-forget communication pattern. Every prior async operation (Chapter 12's planning graph) still had a clear requester waiting for a result via polling. A notification has no such waiting party — it's dispatched, and the system moves on regardless of whether the recipient ever sees it. This is also the first chapter to handle failure of an external dependency that isn't an LLM provider, and it uses a genuinely different retry tool for it: Celery's own native task retry, not Chapter 11's `tenacity`, because the granularity of what's being retried is different.

---

## 1. Learning Objective

By the end of this chapter you will be able to:
- Separate "record that something should be sent" (fast, synchronous) from "actually send it" (slow, unreliable, async) as two distinct steps with two distinct failure profiles.
- Choose between `tenacity` (Chapter 11, retrying a call *within* an already-async unit of work) and Celery's own task-level retry (retrying the *entire async unit of work* itself), and explain why each fits its own situation.
- Build a single-door abstraction around an external delivery channel (email), matching the same "one seam, swappable later" discipline as `GroqClient` (Chapter 11) and the weather tool (Chapter 14).
- Wire a one-directional trigger from `ai_agents` into a new domain app, consistent with the dependency direction established since Chapter 12 (and contrasted with Chapter 19's deliberate bidirectional exception for `chat`).

---

## 2. Theory

### 2.1 Why "Create the Record" and "Actually Send It" Are Two Separate Steps (ELI10)

Imagine writing a birthday card versus actually mailing it. Writing it is fast and always succeeds — you have full control over a piece of paper and a pen. Mailing it depends on the postal service, which might be delayed, might lose it, might need a retry. Treating "record that a notification should exist" (a fast database write, always succeeds if the database is up) as separate from "deliver it" (a slow, unreliable call to an external email provider) means a notification's *existence* is never at the mercy of the delivery channel's reliability — a user can always see "you have a notification, currently pending delivery" even if the actual email hasn't gone out yet.

### 2.2 Why This Chapter Uses Celery's Own Retry, Not `tenacity`

Chapter 11's `tenacity`-based retry wraps a *synchronous function call happening inside an already-dispatched Celery task* — the task itself doesn't get re-queued; only the inner HTTP call to Groq retries, quickly, before the task continues. A notification's "send" operation, by contrast, **is itself** the async unit of work — there's no larger task wrapping it. Retrying it means re-queueing the *entire task* to run again later, which is exactly what Celery's own `autoretry_for`/`retry_backoff` task options are built for. Using the tool that matches the actual granularity being retried — an inner call versus a whole task — rather than reflexively reusing Chapter 11's `tenacity` pattern everywhere, is the real lesson here.

### 2.3 Why `Notification.user` Uses `CASCADE`, Unlike `AgentRun.triggered_by`'s `SET_NULL` (Chapter 12)

Chapter 12 chose `SET_NULL` for `AgentRun.triggered_by` because an agent run's *history* has ongoing debugging/analytics value even after the triggering user is gone — the run itself still happened and is worth keeping. A notification has no such independent value: it exists *entirely* to inform a specific person, and if that person's account is gone, there is no one left to notify and nothing meaningful preserved by keeping the row. `CASCADE` here isn't a lesser choice than `SET_NULL` — it's the *correct* one for what this specific model represents, the same "decide per-relationship, not by blanket rule" discipline behind every `on_delete` choice in this project since Chapter 5.

---

## 3. Architecture Decision

**Decision:** `Notification` creation (`create_notification`) is synchronous and always succeeds if the database is reachable; actual delivery (`send_notification_task`) is dispatched separately via Celery, with its own independent retry policy.

**Decision:** Email sending goes through a single function, `apps/notifications/backends.py::send_email`, wrapping Django's built-in `django.core.mail.send_mail` — no new external package, matching the same "use what's already available before reaching for a new dependency" instinct as this project's other single-seam abstractions.

**Decision:** `send_notification_task` uses Celery's `autoretry_for` + `retry_backoff`, capped at 3 attempts, after which the `Notification` is marked `failed` permanently — no infinite retry, matching the same "always terminate, never leave something stuck in an in-progress state forever" discipline as Chapter 12's `AgentRun` handling.

**Decision:** `ai_agents` triggers a notification on planning success by calling `apps.notifications.services.create_notification()` directly — a one-directional dependency (`ai_agents → notifications`), consistent with every other domain app `ai_agents` already reaches into (Chapters 12-16), and explicitly *not* like Chapter 19's `chat` exception, since `notifications` never needs to call back into `ai_agents`.

---

## 4. Why Before How

| Step | Why it must happen in this order |
|---|---|
| Define `Notification` model + migration | Needed before any service function can persist anything |
| Write `apps/notifications/backends.py` | Needed before the Celery task can actually attempt delivery |
| Write `apps/notifications/services.py` | Needed before the task or any trigger point can call it |
| Write `apps/notifications/tasks.py` | Needed before any trigger point can dispatch delivery |
| Wire the trigger into `apps/ai_agents/services.py` | Needs the whole notifications pipeline already working, to plug into it |
| Build the read-facing API (list, mark-read) | Last — the user-facing surface on top of everything else |

---

## 5. File Structure

```
apps/notifications/
├── __init__.py
├── apps.py
├── models.py                    # Notification
├── backends.py                    # send_email — THE single door to the email provider
├── services.py                     # create_notification, mark_as_read
├── tasks.py                         # send_notification_task (Celery, own retry policy)
├── serializers.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_backends.py
    ├── test_services.py
    ├── test_tasks.py
    └── test_views.py

apps/ai_agents/
└── services.py                    # MODIFIED — notification trigger on planning success
```

---

## 6. Folder Location

New files under `apps/notifications/` (already scaffolded empty since Chapter 2).

---

## 7. Terminal Commands

```bash
docker compose exec web python manage.py makemigrations notifications
docker compose exec web python manage.py migrate

docker compose exec web python manage.py test apps.notifications apps.ai_agents -v 2
```

---

## 8. Docker Commands

```bash
docker compose restart web celery
```

---

## 9. Expected Output

```
$ docker compose exec web python manage.py shell -c "
from apps.notifications import services
from django.contrib.auth import get_user_model
user = get_user_model().objects.first()
n = services.create_notification(user=user, notification_type='trip_plan_ready', subject='Your trip is ready!', body='...')
print(n.status)
"
pending

# after the Celery task runs:
$ docker compose exec web python manage.py shell -c "
from apps.notifications.models import Notification
print(Notification.objects.first().status)
"
sent
```

---

## 10. Code

### 10.1 `apps/notifications/models.py`

```python
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class NotificationType(models.TextChoices):
    TRIP_PLAN_READY = "trip_plan_ready", "Trip Plan Ready"
    TRIP_PLAN_FAILED = "trip_plan_failed", "Trip Plan Failed"
    SHARE_LINK_CREATED = "share_link_created", "Share Link Created"
    GENERIC = "generic", "Generic"


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    # SMS, push, WhatsApp reserved per Architecture Handbook §13 —
    # not implemented yet, deliberately present so a future channel
    # doesn't require a schema migration just to be choosable.


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Notification(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    user uses CASCADE, unlike AgentRun.triggered_by's SET_NULL
    (Chapter 12) — see Chapter 22 Theory §2.3 for why this is the
    correct choice for THIS specific relationship, not a
    contradiction of that earlier decision.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices, default=NotificationChannel.EMAIL)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING, db_index=True)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self) -> str:
        return f"{self.notification_type} -> {self.user.email} ({self.status})"
```

**Why `is_read` exists here, unrelated to delivery `status`**: these are two genuinely independent concerns — whether the notification was *successfully delivered* (a system-level fact, `status`) and whether the *user has seen it in their notification list* (a user-level fact, `is_read`). A notification can be `sent` and unread, or (less usefully but still meaningfully) `failed` and the user might still want to dismiss it from their list — conflating the two into one field would lose this real distinction.

### 10.2 `apps/notifications/backends.py`

```python
"""
THE single door to the email provider. If this project ever swaps
from Django's built-in SMTP backend to a dedicated provider (SES,
SendGrid, etc.), ONLY this file changes — same seam discipline as
GroqClient (Chapter 11) and the weather tool (Chapter 14).
"""
from django.conf import settings
from django.core.mail import send_mail


def send_email(*, to: str, subject: str, body: str) -> None:
    """
    Raises on failure — the caller (the Celery task, Section 10.4)
    is responsible for catching and deciding what happens next.
    This function's only job is "attempt delivery," nothing more.
    """
    send_mail(
        subject=subject, message=body, from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to], fail_silently=False,
    )
```

**Why `send_email` deliberately raises rather than returning a boolean success/failure flag**: raising lets the Celery task's own retry machinery (Section 10.4) catch a *specific* exception type and decide the retry policy — a boolean return would require the caller to invent its own way of knowing *why* it failed, losing information a real exception carries naturally. This mirrors Chapter 11's `LLMCallFailed` — a real exception, not a silent `False`.

### 10.3 `apps/notifications/services.py`

```python
from apps.notifications.models import Notification, NotificationChannel, NotificationStatus


def create_notification(
    *, user, notification_type: str, subject: str, body: str,
    channel: str = NotificationChannel.EMAIL,
) -> Notification:
    """
    Fast, synchronous, always succeeds if the database is up — see
    Chapter 22 Theory §2.1 for why this is deliberately separate
    from actual delivery.
    """
    notification = Notification.objects.create(
        user=user, notification_type=notification_type, channel=channel,
        subject=subject, body=body, status=NotificationStatus.PENDING,
    )
    from apps.notifications.tasks import send_notification_task
    send_notification_task.delay(notification_id=str(notification.id))
    return notification


def mark_as_read(*, notification: Notification) -> Notification:
    notification.is_read = True
    notification.save(update_fields=["is_read", "updated_at"])
    return notification
```

**Why the Celery task import is deferred inside `create_notification`, not at module level**: same defensive pattern already used in Chapter 12's Celery task and Chapter 19's chat views — avoids any risk of an import-order issue during Django's app-loading sequence, applied here consistently rather than reasoned about fresh each time.

### 10.4 `apps/notifications/tasks.py`

```python
"""
Celery's OWN retry mechanism, not tenacity — see Chapter 22 Theory
§2.2 for why this is the correct tool for retrying an entire async
unit of work, distinct from Chapter 11's inner-call retry pattern.
"""
from smtplib import SMTPException

from celery import shared_task
from django.utils import timezone


@shared_task(
    bind=True,
    autoretry_for=(SMTPException, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def send_notification_task(self, notification_id: str):
    from apps.notifications.backends import send_email
    from apps.notifications.models import Notification, NotificationStatus

    notification = Notification.objects.get(pk=notification_id)

    try:
        send_email(to=notification.user.email, subject=notification.subject, body=notification.body)
    except (SMTPException, ConnectionError):
        # Celery's autoretry_for handles the retry automatically. If
        # this is the FINAL attempt (max_retries exhausted), Celery
        # re-raises here instead of retrying again — caught below.
        if self.request.retries >= self.max_retries:
            notification.status = NotificationStatus.FAILED
            notification.error_message = "Delivery failed after maximum retry attempts."
            notification.save(update_fields=["status", "error_message", "updated_at"])
        raise
    else:
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at", "updated_at"])
```

**Why `retry_backoff=True` with `retry_backoff_max=60` instead of a fixed delay between retries**: an email provider hiccup is often transient and resolves within seconds to a couple of minutes — exponential backoff (capped at 60s here, deliberately shorter than Chapter 11's LLM backoff, since email delivery failures are typically shorter-lived than LLM provider issues) gives the provider a growing amount of time to recover without either retrying too aggressively or waiting unreasonably long.

**Why the `except` block checks `self.request.retries >= self.max_retries` before marking the notification `failed`**: Celery's `autoretry_for` re-raises the *same* exception on each attempt, running this task function again from the top — the `except` block here only executes meaningfully on retry attempts, and specifically marks `failed` only on the *final* one, since intermediate retries shouldn't permanently mark a notification as failed while retries are still ongoing.

### 10.5 `apps/ai_agents/services.py` (addition — the trigger)

```python
def _notify_planning_succeeded(*, trip) -> None:
    from apps.notifications.services import create_notification
    from apps.notifications.models import NotificationType

    create_notification(
        user=trip.user,
        notification_type=NotificationType.TRIP_PLAN_READY,
        subject=f"Your itinerary for {trip.title} is ready!",
        body=f"Your AI-generated plan for {trip.title} ({trip.start_date} to {trip.end_date}) is ready to view.",
    )
```

Called at the end of `run_travel_planner`, only on success:

```python
    else:
        agent_run.status = AgentRunStatus.SUCCEEDED
        _notify_planning_succeeded(trip=trip)
    finally:
        agent_run.completed_at = timezone.now()
        agent_run.save(update_fields=["status", "error_message", "completed_at"])
```

**Why `_notify_planning_succeeded` is called in the `else` block (only-on-success), not `finally` (always)**: a failed or needs-review planning run shouldn't tell the user "your itinerary is ready" — that would be actively misleading. A failure-path notification (`TRIP_PLAN_FAILED`) is a reasonable, trivial future addition using the exact same `create_notification` call with a different `notification_type`, deliberately left as a one-line extension rather than built now, to keep this chapter's scope focused on the mechanism itself.

**Why this is a one-directional `ai_agents → notifications` call, not routed any other way**: `notifications` never needs anything back from `ai_agents` — this is the normal, established dependency shape (Chapters 12-16), explicitly *not* like Chapter 19's `chat` exception, worth restating so the two different dependency shapes in this project (one-directional vs. Chapter 19's justified bidirectional case) stay clearly distinguished.

### 10.6 `apps/notifications/serializers.py`

```python
from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "subject", "body", "status", "is_read", "created_at"]
        read_only_fields = ["id", "notification_type", "subject", "body", "status", "created_at"]
        # is_read is the ONLY writable field — same pattern as
        # Chapter 16's PackingItemSerializer
```

### 10.7 `apps/notifications/views.py`

```python
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get("unread") == "true"
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_pk):
        notification = get_object_or_404(Notification, pk=notification_pk, user=request.user)
        updated = services.mark_as_read(notification=notification)
        return Response(NotificationSerializer(updated).data)
```

### 10.8 `apps/notifications/urls.py`

```python
from django.urls import path

from apps.notifications.views import NotificationListView, NotificationMarkReadView

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<uuid:notification_pk>/read/", NotificationMarkReadView.as_view(), name="mark-read"),
]
```

### 10.9 `config/urls.py` (addition)

```python
path("api/v1/notifications/", include("apps.notifications.urls")),
```

### 10.10 `apps/notifications/admin.py`

```python
from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "notification_type", "channel", "status", "is_read", "created_at"]
    list_filter = ["notification_type", "channel", "status", "is_read"]
    search_fields = ["user__email", "subject"]
    readonly_fields = ["sent_at", "error_message", "created_at", "updated_at"]
```

---

## 11. Code Walkthrough

- **This chapter's retry mechanism (Celery's `autoretry_for`) and Chapter 11's (`tenacity`) solve genuinely different problems, not the same problem with two different tools**: `tenacity` retries a call *inside* a task without re-running the whole task; Celery's own retry re-runs the *entire task function* from the top. Confusing these — reaching for `tenacity` here, or Celery's retry inside `GroqClient` — would produce awkward, harder-to-reason-about code. Recognizing "what exactly is the unit being retried" is the actual skill, not memorizing which library to import.
- **`send_email`'s deliberate choice to raise rather than return a boolean is what makes Celery's `autoretry_for` work at all**: `autoretry_for` operates on *exception types* — if `send_email` swallowed its own errors and returned `False`, Celery would have nothing to catch and retry on, silently breaking the whole retry chain. This is worth tracing through as a concrete example of how a seemingly small API design choice (raise vs. return) has real downstream consequences.
- **The `else`-not-`finally` placement of the success notification (Section 10.5) is a small but meaningful correctness detail**: it would be easy to accidentally place this in `finally` "to make sure it always runs," which would be actively wrong here — always double-check which of Python's `try/except/else/finally` blocks actually matches the semantic you need, not just which one "runs no matter what."

---

## 12. Common Errors

| Error | Cause | Fix |
|---|---|---|
| Notification stuck in `pending` forever | Celery worker not running, or task never dispatched (import error in `create_notification`) | Confirm `docker compose ps celery` shows the worker up; check worker logs for a task registration error |
| Notification incorrectly marked `failed` after only one attempt | `self.request.retries >= self.max_retries` check has an off-by-one error, or `max_retries` misconfigured | Confirm `max_retries=3` on the task decorator and trace through the retry count logic carefully |
| Real emails not appearing in dev | `EMAIL_BACKEND` still pointing at SMTP with no real credentials configured locally | Confirm dev settings use `django.core.mail.backends.console.EmailBackend`, printing emails to the console instead of attempting real delivery |
| User gets a "trip ready" notification for a run that actually failed | Notification call accidentally placed in `finally` instead of the `else` branch | Move it back to `else` — this is the exact mistake Section 11 warns about |

---

## 13. Debugging

```bash
# 1. Confirm the backend raises (not swallows) on a bad configuration
docker compose exec web python manage.py shell -c "
from apps.notifications.backends import send_email
try:
    send_email(to='test@example.com', subject='Test', body='Hello')
    print('sent (check console backend output above)')
except Exception as e:
    print('raised as expected:', e)
"

# 2. Force a failure and confirm the task's retry/final-failure behavior
docker compose exec web python manage.py shell -c "
from apps.notifications import services
from django.contrib.auth import get_user_model
user = get_user_model().objects.first()
n = services.create_notification(user=user, notification_type='generic', subject='Test', body='Test')
print(n.status)
"
```

**Rollback strategy:** a `failed` notification has no cascading effect on anything else in the system — the trip, itinerary, and every other piece of data are completely unaffected by a notification never being delivered, by design (Theory §2.1's separation).

---

## 14. Testing

### 14.1 `apps/notifications/tests/test_models.py`

```python
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import Notification, NotificationStatus

User = get_user_model()


class NotificationModelTests(TestCase):
    def test_defaults(self):
        user = User.objects.create_user(email="n@example.com", password="pass1234")
        notification = Notification.objects.create(
            user=user, notification_type="generic", subject="Test", body="Test body",
        )
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertFalse(notification.is_read)

    def test_cascade_delete_with_user(self):
        user = User.objects.create_user(email="n2@example.com", password="pass1234")
        notification = Notification.objects.create(user=user, notification_type="generic", subject="Test", body="Test")
        user.delete()
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())
```

### 14.2 `apps/notifications/tests/test_backends.py`

```python
from django.core import mail
from django.test import TestCase, override_settings

from apps.notifications.backends import send_email


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendEmailBackendTests(TestCase):
    def test_send_email_delivers_via_configured_backend(self):
        send_email(to="test@example.com", subject="Hello", body="Test body")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Hello")
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
```

### 14.3 `apps/notifications/tests/test_services.py`

```python
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications import services
from apps.notifications.models import NotificationStatus

User = get_user_model()


class CreateNotificationServiceTests(TestCase):
    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_create_notification_dispatches_task(self, mock_delay):
        user = User.objects.create_user(email="s@example.com", password="pass1234")
        notification = services.create_notification(
            user=user, notification_type="generic", subject="Test", body="Body",
        )
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        mock_delay.assert_called_once_with(notification_id=str(notification.id))

    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_mark_as_read(self, mock_delay):
        user = User.objects.create_user(email="s2@example.com", password="pass1234")
        notification = services.create_notification(user=user, notification_type="generic", subject="T", body="B")
        self.assertFalse(notification.is_read)
        services.mark_as_read(notification=notification)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
```

### 14.4 `apps/notifications/tests/test_tasks.py`

```python
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.tasks import send_notification_task

User = get_user_model()


class SendNotificationTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="t@example.com", password="pass1234")
        self.notification = Notification.objects.create(
            user=self.user, notification_type="generic", subject="Test", body="Test body",
        )

    @patch("apps.notifications.backends.send_email")
    def test_successful_send_marks_sent(self, mock_send_email):
        send_notification_task.apply(kwargs={"notification_id": str(self.notification.id)})
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(self.notification.sent_at)

    @patch("apps.notifications.backends.send_email")
    def test_permanent_failure_after_max_retries_marks_failed(self, mock_send_email):
        from smtplib import SMTPException
        mock_send_email.side_effect = SMTPException("provider down")

        # .apply() with throw=False runs synchronously without Celery's
        # real retry queueing — this test exercises the FINAL-attempt
        # failure path directly by simulating an exhausted retry count.
        with patch.object(send_notification_task, "request") as mock_request:
            mock_request.retries = 3
            try:
                send_notification_task.run(notification_id=str(self.notification.id))
            except SMTPException:
                pass

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, NotificationStatus.FAILED)
```

### 14.5 `apps/ai_agents/tests/test_services.py` (addition)

Added as two new methods on Chapter 12's `RunTravelPlannerServiceTests` class:

```python
    @patch("apps.notifications.services.create_notification")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_successful_run_triggers_ready_notification(self, mock_run_graph, mock_create_notification):
        mock_run_graph.return_value = {
            "itinerary_plan": ItineraryPlanSchema(days=[
                ItineraryDaySchema(day_number=1, date=self.trip.start_date, items=[
                    ItineraryItemSchema(title="Check in")
                ])
            ]),
        }
        run_travel_planner(trip=self.trip)
        mock_create_notification.assert_called_once()
        call_kwargs = mock_create_notification.call_args.kwargs
        self.assertEqual(call_kwargs["notification_type"], "trip_plan_ready")

    @patch("apps.notifications.services.create_notification")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_failed_run_does_not_trigger_ready_notification(self, mock_run_graph, mock_create_notification):
        from ai.exceptions import LLMCallFailed
        mock_run_graph.side_effect = LLMCallFailed("provider down")
        run_travel_planner(trip=self.trip)
        mock_create_notification.assert_not_called()
```

Run everything:

```bash
docker compose exec web python manage.py test apps.notifications apps.ai_agents -v 2
```

---

## 15. Git Commit

```bash
git add apps/notifications/ apps/ai_agents/services.py config/urls.py
git commit -m "feat(notifications): outbound dispatch, first fire-and-forget pattern

- Notification: user=CASCADE (contrast with AgentRun.triggered_by's
  SET_NULL, Chapter 12) — a notification has no independent value
  once there's no one left to notify, unlike an agent run's history
- is_read tracked separately from delivery status — two genuinely
  independent facts (was it delivered vs has the user seen it)
- backends.py: single door to email delivery (django.core.mail, no
  new dependency), raises rather than returning bool — required for
  Celery's autoretry_for to have something to catch
- create_notification: fast, synchronous, always succeeds if the DB
  is up; delivery is a SEPARATE Celery-dispatched step — the record
  of a notification's existence never depends on delivery reliability
- send_notification_task uses CELERY'S OWN retry (autoretry_for,
  retry_backoff), NOT tenacity — different tool for a different
  granularity: retrying an entire async unit of work, not an inner
  call within one (contrast with Chapter 11's GroqClient retry)
- Success notification wired into ai_agents.run_travel_planner's
  else branch (only-on-success), NOT finally — tested explicitly
  that a failed run does not trigger a 'ready' notification
- One-directional ai_agents -> notifications dependency, consistent
  with Chapters 12-16, explicitly contrasted with Chapter 19's
  justified bidirectional chat <-> ai_agents exception

Chapter 22 of Implementation Bible."
```

---

## 16. Checklist

- [ ] `Notification.user` is `CASCADE`; reasoning contrasted explicitly against `AgentRun.triggered_by`'s `SET_NULL`
- [ ] `is_read` and `status` are confirmed independent fields, not conflated
- [ ] `backends.send_email` raises on failure, never returns a boolean
- [ ] `create_notification` always succeeds synchronously (if DB is up); delivery is a separate dispatched task, verified by a test asserting `.delay()` was called
- [ ] `send_notification_task` uses Celery's own `autoretry_for`/`retry_backoff`, not `tenacity`
- [ ] Final-retry failure correctly marks the notification `failed`, tested explicitly
- [ ] Success notification triggers only on the `else` (success) branch — verified by a test that a failed run does NOT notify
- [ ] All tests passing
- [ ] Commit made

---

## 17. Next Chapter Preview

**Chapter 23 — `bookings` App (Placeholder)** builds the smallest chapter in the entire project by design: a future-facing model shell with no external integration at all, existing purely to reserve the shape Architecture Handbook §13's marketplace roadmap will eventually need — the deliberate, minimal counterpart to every other chapter's full build-out, worth treating as its own kind of lesson in knowing when *not* to build more than the moment requires. Say **"Continue to Chapter 23"** when ready.
