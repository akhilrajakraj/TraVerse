# Chapter 22 — Notifications Domain Implementation

## Architectural Realization

The implementation is organized around a strict separation between domain persistence, delivery orchestration, external transport, and HTTP presentation.

```text
apps/notifications/
├── models.py
├── backends.py
├── services.py
├── tasks.py
├── serializers.py
├── views.py
├── urls.py
├── admin.py
└── migrations/
    └── 0001_initial.py
```

The AI planning application is also modified at its Django-facing service boundary to create a notification after a successful planning result.

## Domain Model

`Notification` inherits `UUIDPrimaryKeyModel` and `TimeStampedModel`. This keeps notification identity consistent with the platform's shared identity convention while providing creation and modification timestamps without duplicating infrastructure fields.

The model contains:

- `user` — the notification recipient, using the configured authentication model and `CASCADE` deletion.
- `notification_type` — a constrained semantic category such as `trip_plan_ready`, `trip_plan_failed`, `share_link_created`, or `generic`.
- `channel` — the delivery channel; the current implementation supports email.
- `subject` and `body` — the persisted notification content.
- `status` — `pending`, `sent`, or `failed`.
- `is_read` — recipient-facing read state, independent from delivery status.
- `sent_at` — timestamp recorded only after successful delivery.
- `error_message` — persisted delivery failure detail.

The model orders notifications newest first and defines a composite index over `(user, is_read)`. This supports the principal read-facing query pattern: retrieve notifications belonging to one user, optionally restricted to unread records.

`CASCADE` is appropriate for `Notification.user` because the notification has no independent business purpose after its recipient account has been removed. This differs from historical records such as an `AgentRun`, where retaining execution history after the initiating user disappears can still have operational value.

## Notification Creation Service

`create_notification()` is the synchronous domain entry point for notification creation.

Its responsibility is deliberately narrow:

```text
create_notification()
        │
        ├── Notification.objects.create(..., status=PENDING)
        │
        └── send_notification_task.delay(notification_id=<UUID>)
```

The notification record is persisted before the asynchronous task is dispatched. The Celery task receives the notification UUID rather than a fully serialized model instance. The worker therefore resolves the authoritative database record when execution begins.

This sequence gives the system a durable representation of the notification before delivery starts and keeps Celery messages small and stable.

The service also exposes `mark_as_read()`. This operation modifies only `is_read` and `updated_at`, leaving delivery state untouched. Read state therefore cannot accidentally be interpreted as delivery confirmation.

## Delivery Backend Boundary

`apps.notifications.backends.send_email_notification()` is the concrete email boundary.

The function accepts a `Notification` and maps its persisted subject, body, and recipient to Django's `send_mail`. It uses `settings.DEFAULT_FROM_EMAIL` and explicitly sets `fail_silently=False`.

The backend does not update `Notification.status`, `sent_at`, or `error_message`. It either completes the delivery operation or propagates the delivery exception to its caller.

This makes the backend a transport adapter rather than a domain service. A transport implementation can therefore change without moving delivery-state policy into the transport layer.

## Celery Delivery Task

`send_notification_task` is declared as a shared Celery task with:

- `bind=True`
- `autoretry_for=(Exception,)`
- exponential retry backoff
- `max_retries=3`

The task resolves the notification by UUID and first checks whether it is already `SENT`. A previously successful notification exits without invoking the external backend. This provides an explicit idempotency guard against duplicate delivery attempts after successful completion.

For a successful delivery, the task records:

```text
PENDING → SENT
         sent_at = current time
         error_message = empty
```

For a delivery exception, it records:

```text
PENDING / retryable state → FAILED
                            error_message = exception text
```

The exception is then re-raised so Celery's retry machinery can recognize the failed task and schedule another attempt. The persisted `FAILED` state records the latest observed delivery failure even while the task remains eligible for retry.

A successful retry clears the previous error message and establishes `sent_at`. The tests explicitly verify this recovery behaviour.

## AI Planning Integration

The AI planning workflow remains responsible for planning. Notification creation is performed at the Django-facing `apps.ai_agents.services` boundary after a successful planning result has been persisted.

The notification call is intentionally directed to `apps.notifications.services.create_notification()` rather than to the Celery task or email backend. This preserves the dependency hierarchy:

```text
AI application service
        ↓
notification domain service
        ↓
Celery delivery task
        ↓
email backend
```

The AI package itself does not acquire a dependency on Django notification models or transport details.

Failure and review outcomes are treated differently from successful planning. The current tests verify that successful planning creates the expected `trip_plan_ready` notification, while failure and review paths do not incorrectly create that success notification.

## Read-Facing API

The HTTP surface contains two authenticated operations:

```text
GET  /api/notifications/
POST /api/notifications/<uuid>/read/
```

The list view applies ownership at queryset construction:

```text
Notification.objects.filter(user=request.user)
```

An optional `unread=true` query parameter adds `is_read=False` filtering.

The mark-read view performs the same ownership restriction during lookup. Consequently, another user's notification is indistinguishable from a missing object at the HTTP boundary and produces `404` rather than exposing the existence of another user's notification.

The serializer is read-oriented. Notification content and delivery state are read-only to API consumers; the user-facing mutation supported by this surface is the read-state transition implemented through the service layer.

## Administrative Surface

The Django admin registration provides operational visibility over notification records. It exposes recipient, notification type, channel, delivery status, read state, delivery timestamp, and creation time, with filters and search fields for recipient and message content.

Infrastructure-managed fields such as the UUID and timestamps are read-only. `list_select_related = ("user",)` prevents the principal recipient display from requiring a separate database lookup per row.

## Migration Boundary

The application has an initial migration creating the notification table. Validation evidence confirms that the migration is discovered and applied when the test database is created.

The migration is part of the application boundary rather than an operational afterthought: without it, model-level correctness cannot be established against PostgreSQL because the relation does not exist.

## Design Rationale Summary

| Decision | Rationale |
|---|---|
| Persist before dispatch | Makes notification existence durable before external delivery begins. |
| Pass UUID to Celery | Avoids serializing ORM state and lets the worker resolve current database state. |
| Backend owns delivery only | Prevents transport code from owning domain lifecycle policy. |
| Celery owns retry | The whole delivery operation is the asynchronous unit of work. |
| Guard `SENT` | Prevents repeat delivery after successful completion. |
| Separate `status` and `is_read` | Delivery and user interaction are independent concerns. |
| Queryset ownership scoping | Prevents cross-user notification disclosure at the data-access boundary. |
| Service-layer mark-read | Keeps domain mutation outside the HTTP presentation layer. |
| Single email backend seam | Isolates external transport choice from the notification domain. |
