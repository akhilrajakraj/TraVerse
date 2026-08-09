# Chapter 22 — Notifications Engineering Lessons

## Durable Intent and External Side Effect Are Different Responsibilities

A notification record expresses durable application intent: a user should have a notification. Email delivery expresses an external side effect: a transport should attempt to communicate that notification.

Separating these concerns prevents transport availability from determining whether the application can represent the event. This pattern generalizes to other unreliable integrations where the application must preserve intent independently from execution.

## Retry Granularity Must Match the Failure Boundary

The platform already uses retry mechanisms inside other asynchronous workflows. Notifications demonstrate why retry technology should be selected according to the unit of work being retried.

The email operation is itself the Celery unit of work. Celery's task-level retry therefore fits naturally. A nested retry library would introduce another failure-control layer without representing a different architectural boundary.

The reusable principle is not a preference for one retry library. It is alignment between retry granularity and responsibility.

## External Transport Should Be Behind a Stable Application Seam

`send_email_notification()` isolates the concrete mail transport from notification lifecycle policy. The notification domain does not need to know whether Django ultimately uses SMTP, a provider adapter, or another transport implementation.

This keeps provider-specific behaviour at the infrastructure edge and makes future transport changes localized.

## Delivery State and User State Must Remain Independent

`status` answers a system question: what happened to delivery? `is_read` answers a user question: has the recipient consumed the notification through the application interface?

Combining these concepts would create ambiguous states and make future channels or user experiences harder to model. Independent state fields preserve the domain distinction.

## Idempotency Is an Application Property

The `SENT` guard demonstrates that task infrastructure alone does not establish the required semantics for an external side effect. The application must define what repeated execution means and prevent repeated delivery where appropriate.

The same principle applies to future notification channels and other asynchronous integrations.

## Ownership Is Part of the Data Model's Operational Meaning

The notification belongs to a user, and that relationship is not merely relational metadata. It defines the security boundary for API retrieval and mutation.

The list query and mark-read lookup therefore incorporate ownership directly. This is preferable to relying on a later application-layer check because the unauthorized record never enters the operation's effective queryset.

## Integration Points Should Depend on Domain Services

The AI planning workflow calls the notification service rather than reaching into models, tasks, or email infrastructure. This keeps the initiating domain coupled to the notification capability rather than to its implementation details.

That distinction supports future changes such as different delivery channels, batching, scheduling, or alternative notification providers without requiring every producer to change.

## Failure Evidence Is Part of Operational State

`error_message`, `sent_at`, and `status` provide operational evidence about the delivery lifecycle. Persisting this information turns an external delivery failure from an ephemeral worker exception into inspectable application state.

This supports debugging, administrative inspection, and future operational tooling.

## Integration Tests Should Validate Boundaries, Not Replace Unit Tests

The notification test suite separates model, service, backend, task, view, and integration concerns. The integration tests then verify that those boundaries cooperate across the full lifecycle.

This gives failures a useful diagnostic location: model failures indicate domain persistence issues, backend failures indicate transport mapping issues, task failures indicate asynchronous lifecycle issues, and integration failures indicate boundary mismatches.

## Schema Validation Is an Engineering Concern

The first notification test run failed because the database relation did not exist. The subsequent successful run demonstrates why migrations belong in the validation chain.

A model that is correct in Python but absent from PostgreSQL is not a functioning Django domain component. Schema synchronization is therefore part of correctness, not merely deployment preparation.
