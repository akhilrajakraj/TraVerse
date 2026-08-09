# Chapter 22 — Notifications Troubleshooting Knowledge

## 1. Notification Tests Failed Because the Database Table Did Not Exist

### Observation

The initial notification model test run discovered 12 tests, but every model test failed with PostgreSQL reporting that the `notifications_notification` relation did not exist.

### Root Cause

The model and tests existed before the corresponding database migration had been applied to the test database. The failure was therefore not a model-behaviour defect; it was an environment/schema synchronization defect.

### Framework Behaviour

Django's test runner constructs a dedicated test database and applies the migrations that Django knows about. A model definition alone does not create a PostgreSQL table. The absence of a migration leaves the ORM model and database schema out of agreement.

### Resolution

The Notifications initial migration was created and included in the migration graph. Subsequent test runs show `notifications.0001_initial` being applied successfully before notification tests execute.

### Architectural Improvement

Migration creation and migration validation are treated as part of feature completion rather than as a separate database-maintenance phase.

### Engineering Principle

A Django application's domain model is not operationally complete until its schema representation is versioned and verified against the target database engine.

---

## 2. Delivery Failure Must Not Be Converted Into a Successful Notification

### Observation

The email backend can raise a runtime delivery exception. A notification must retain evidence of that failure instead of being marked `SENT`.

### Root Cause

Email delivery is an external side effect whose success cannot be inferred from the existence of the database record.

### Framework Behaviour

Django's `send_mail` raises when `fail_silently=False`. The notification backend intentionally allows that exception to propagate. The Celery task catches it, persists `FAILED` and the error message, and re-raises the exception.

### Resolution

Delivery state transitions are owned by `send_notification_task`, not `send_email_notification`. The backend test suite verifies that the backend itself does not modify notification state, while task tests verify `FAILED` persistence and exception propagation.

### Architectural Improvement

The transport adapter is prevented from becoming a second lifecycle manager. Delivery execution and delivery-state policy remain separate.

### Engineering Principle

External integrations should report failure to the layer that owns domain policy rather than silently mutating domain state themselves.

---

## 3. A Successful Retry Must Clear Stale Failure Information

### Observation

A notification can have an existing error message from an earlier delivery attempt and later succeed.

### Root Cause

Failure information is historical state attached to the current delivery lifecycle. Leaving it populated after success would make the record appear failed even when the latest delivery completed successfully.

### Framework Behaviour

Celery may execute the same task more than once because delivery is configured for automatic retry. The task therefore has to establish a complete successful terminal state on every successful attempt.

### Resolution

On successful delivery the task writes `SENT`, sets `sent_at`, and clears `error_message` in one database update.

### Architectural Improvement

The success transition is treated as a state normalization operation rather than only a status-field assignment.

### Engineering Principle

Retryable workflows must define both failure persistence and successful recovery semantics; otherwise stale operational state can survive a successful retry.

---

## 4. Duplicate Delivery Must Be Guarded After Success

### Observation

The delivery task can be invoked again for a notification whose status is already `SENT`.

### Root Cause

Asynchronous systems can encounter duplicate execution requests. A durable success marker is therefore required to distinguish an unprocessed notification from one that has already completed delivery.

### Framework Behaviour

Celery task execution is asynchronous and does not by itself provide the application-specific guarantee that an external side effect will never be requested twice.

### Resolution

The task checks `NotificationStatus.SENT` before invoking the email backend and returns immediately when the notification is already delivered.

### Architectural Improvement

Idempotency is implemented at the side-effect boundary rather than assumed from task dispatch semantics.

### Engineering Principle

Any asynchronous task that performs an external side effect should define an explicit idempotency strategy appropriate to that side effect.

---

## 5. Cross-User Notification Access Must Resolve as a Missing Resource

### Observation

An authenticated user attempting to mark another user's notification as read receives `404`, and the other user's record remains unchanged.

### Root Cause

Notification ownership is a security boundary. A lookup by UUID alone would permit an authenticated user who knows another notification's identifier to operate on it.

### Framework Behaviour

Django's `get_object_or_404` evaluates the queryset supplied to it. By including both the notification primary key and `user=request.user` in that queryset, the view constrains the lookup to the current user's ownership boundary.

### Resolution

Both list retrieval and mark-read lookup are scoped to the authenticated user. The API therefore does not reveal another user's notification through a successful object lookup.

### Architectural Improvement

Ownership is enforced where records are selected, rather than fetched globally and checked later.

### Engineering Principle

Multi-tenant or user-owned data should be constrained at the query boundary whenever the ownership relationship is part of the access rule.
