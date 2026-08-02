# Chapter 09 — Budget Management

## Overview

The Budget application introduces financial planning into the TraVerse platform by modelling estimated travel costs independently from trip scheduling and destination management.

Previous chapters established the structural components required to organize travel information. Trips define ownership, lifecycle, and overall travel context, while the Itinerary application models day-by-day travel activities. The Budget domain extends these capabilities by providing structured financial planning without coupling monetary information directly to itinerary or destination data.

Rather than storing financial information within the Trip aggregate itself, the platform introduces a dedicated Budget aggregate responsible for managing planned expenditure together with individual cost entries. This separation preserves clear domain boundaries while enabling future financial capabilities to evolve independently of travel scheduling.

---

# Purpose of the Budget Domain

Travel planning consists of both logistical organization and financial estimation.

While itineraries describe *what* a traveler intends to do, budgets describe *how much* those activities are expected to cost.

The Budget application provides this financial perspective through two primary business entities:

- one Budget for every Trip
- multiple Budget Line Items representing individual planned expenses

Each budget acts as a financial aggregate beneath its parent trip while remaining isolated from unrelated platform concerns.

---

# Aggregate Structure

The application introduces a dedicated financial aggregate.

```text
Trip
│
└── Budget
      │
      ├── Budget Line Item
      ├── Budget Line Item
      ├── Budget Line Item
      └── Budget Line Item
```

The Trip remains the aggregate root responsible for ownership and lifecycle management.

The Budget application extends this aggregate by introducing structured financial information while preserving the ownership model established in earlier chapters.

---

# Relationship with Existing Applications

The Budget application integrates with several previously established domains.

## Accounts

Authentication and ownership continue to originate from the Accounts application.

Every budget ultimately belongs to the authenticated owner of its parent trip.

The Budget application therefore never manages user identity directly.

---

## Trips

The Trips application remains responsible for travel lifecycle management.

Budget extends each trip by introducing financial planning while exposing a synchronized computed budget total for summary and reporting purposes.

---

## Itinerary

The Itinerary application organizes travel activities.

Budget intentionally remains independent of itinerary scheduling.

Although future platform capabilities may estimate costs directly from itinerary activities, the current implementation preserves separation between scheduling and financial planning.

---

## Core

The Budget application continues building upon the shared platform infrastructure introduced throughout previous chapters.

Common abstractions include:

- UUID primary keys
- timestamp inheritance
- centralized exception handling
- shared architectural conventions
- layered application structure

Maintaining these conventions ensures that the Budget domain integrates naturally with the remainder of the platform.

---

# Architectural Capabilities Introduced

This chapter introduces several new architectural concepts beyond simple data persistence.

## Aggregate Synchronization

The application introduces automatic synchronization between related aggregates.

Whenever financial information changes, the Trip aggregate automatically maintains a denormalized summary value representing the total estimated budget.

This synchronization removes the need for repeated aggregation during common read operations.

---

## Event-Driven Domain Behaviour

The Budget application is the first domain within TraVerse to introduce event-driven behaviour through Django signals.

Domain events allow related business entities to remain synchronized while preserving loose coupling between business operations.

Write operations remain focused on creating or modifying business entities, while synchronization responsibilities are delegated to the event layer.

---

## Aggregated Read Models

Financial totals are calculated through dedicated selector modules rather than embedded within views or business services.

Centralizing aggregation logic ensures that every consumer observes identical financial calculations while avoiding duplicated query logic throughout the application.

---

## Denormalized Summary Data

The Trip aggregate maintains a computed budget total alongside detailed budget line items.

This design intentionally introduces controlled denormalization to improve read performance while preserving correctness through automatic synchronization.

---

# Scope of the Chapter

The Budget application focuses exclusively on financial planning.

Its responsibilities include:

- maintaining one budget per trip
- organizing budget line items
- categorizing planned expenses
- calculating aggregated budget totals
- synchronizing financial summaries
- exposing reusable financial APIs

The application intentionally excludes:

- payment processing
- expense reimbursement
- real-world transaction recording
- invoicing
- currency conversion
- financial reporting
- budgeting analytics

These capabilities remain the responsibility of future platform domains.

---

# Platform Significance

The Budget application represents an important architectural milestone within TraVerse.

Earlier chapters introduced hierarchical aggregates together with explicit separation between read operations and write operations.

This chapter extends those principles by introducing event-driven synchronization between aggregates while preserving clear domain boundaries.

Automatic financial synchronization, reusable aggregation logic, and denormalized summary values establish architectural patterns that future platform capabilities—including analytics, artificial intelligence, recommendations, forecasting, and reporting—can build upon without modifying the underlying financial domain.

Rather than functioning solely as a budgeting component, the Budget application establishes the platform's foundational approach to event-driven consistency between related business aggregates.