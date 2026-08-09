# Chapter 22 — Notifications Domain

## Architectural Context

The `notifications` application provides the platform-level boundary for user-facing notification records and their delivery lifecycle. It separates the durable fact that a notification exists from the unreliable operation of delivering that notification through an external channel.

The application therefore sits between domain events that require user awareness and delivery infrastructure. Current consumers include the AI planning workflow, which creates a notification when travel-plan processing reaches a terminal outcome. The notification domain does not own travel planning, itinerary generation, or AI execution; it owns the representation, delivery state, and read state of notifications.

This separation is significant because notification delivery is an external side effect. Database persistence is a local domain operation, while email delivery depends on the configured Django email backend and can fail independently. The architecture preserves that distinction instead of allowing an external transport failure to erase the underlying notification record.

## Domain Responsibilities

The application owns four related responsibilities:

1. **Notification representation** — a UUID-backed `Notification` records its recipient, semantic type, delivery channel, message content, delivery status, read state, delivery timestamp, and failure information.
2. **Notification orchestration** — `create_notification()` persists a pending record and dispatches asynchronous delivery through Celery.
3. **Delivery boundary** — `backends.py` contains the email-specific integration with Django's configured mail backend.
4. **Recipient-facing state** — authenticated API views expose a user's notifications and permit the user to mark an owned notification as read.

These responsibilities remain distinct. The backend performs delivery but does not mutate notification state. The Celery task owns delivery-state transitions. The service layer owns domain operations. The API layer owns authentication, ownership scoping, and serialization.

## Relationships With Existing Applications

The primary dependency direction is:

```text
AI planning workflow
        │
        │ create_notification()
        ▼
notifications service
        │
        ├── persists Notification(PENDING)
        │
        └── dispatches Celery task
                    │
                    ▼
              notification task
                    │
                    ▼
              email backend
                    │
                    ▼
        configured Django mail transport
```

The notification application depends on the shared core UUID and timestamp infrastructure and the configured Django authentication user model. It does not depend on the AI implementation itself.

The AI package therefore remains responsible for producing a planning result, while `apps.ai_agents.services` acts as the Django-facing integration point that can request a notification. This preserves the boundary between the framework-facing application layer and the internal AI package.

## Delivery and Read State

Delivery status and read state intentionally represent different facts.

| Concern | Field | Owner of transition |
|---|---|---|
| Awaiting / delivered / failed | `status` | notification delivery task |
| Time of successful delivery | `sent_at` | notification delivery task |
| Delivery failure detail | `error_message` | notification delivery task |
| User has read the notification | `is_read` | notification service/API |

A notification can therefore be successfully delivered while remaining unread. Conversely, a failed notification remains a durable record and can still be surfaced through the authenticated notification API.

## Architectural Significance

Chapter 22 introduces a genuinely one-way asynchronous side-effect boundary. The initiating workflow does not wait for the external transport to complete. It records the intent, schedules delivery, and continues independently.

The application also establishes a reusable delivery seam. The current channel is email, implemented through Django's `send_mail`. The domain model already represents the delivery channel explicitly, while the concrete backend remains isolated from the service and task layers.

The retry policy is intentionally owned by Celery at task level. The entire delivery operation is the asynchronous unit of work, so a delivery failure causes that unit to be retried rather than introducing a second retry mechanism inside the backend.

## Expected Future Consumers

The notification boundary is suitable for future platform workflows that need asynchronous user communication, including additional trip lifecycle events, document/share-link events, operational alerts, and additional delivery channels. Such consumers should depend on the notification service rather than directly invoking email infrastructure.

The current implementation does not claim those future channels exist. Email is the implemented transport and the only channel represented by the current `NotificationChannel` enumeration.
