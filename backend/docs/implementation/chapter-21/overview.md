# Chapter 21 — Documents App: Overview

## Architectural Context

The `documents` application provides document-oriented capabilities for the TraVerse trip domain. Its responsibilities are itinerary PDF generation and revocable public sharing of trip itineraries.

The application introduces two distinct behaviours:

- PDF generation produces an ephemeral response artifact rather than a persisted file.
- Public itinerary access is capability-based rather than identity-based.

The feature therefore extends the authenticated trip architecture without replacing its ownership model.

## Problem Definition

Trip data is maintained as structured application state. Consumers require a downloadable itinerary document and a shareable representation that can be accessed by someone without a TraVerse account.

Persisting generated PDFs would introduce a second representation of itinerary state that could become stale when the underlying trip changes. The implementation instead generates the PDF from current state when requested.

Public sharing presents a different authorization problem. An unauthenticated request has no user identity against which ownership can be evaluated. The implementation therefore uses a separately generated capability token. Possession of a valid, active, non-expired token authorizes access to the public itinerary representation.

## Domain Responsibilities

The application owns:

- share-link persistence;
- share-token generation;
- share-link revocation;
- share-link expiration state;
- public-token lookup;
- itinerary PDF generation;
- serialization of the deliberately limited public itinerary representation.

It does not own authentication, user identity, trip ownership, or itinerary domain modelling.

## Relationships With Existing Applications

`Trip` supplies the domain object used by PDF generation and public sharing.

The established itinerary selector supplies itinerary data to the public endpoint. Authentication remains responsible for authenticated access to document operations.

## Architectural Significance

Chapter 21 introduces the first intentionally public API surface described by the implementation design. The public endpoint uses `AllowAny`, but access is not unrestricted: the share token functions as a capability secret.

Authenticated endpoints evaluate identity and ownership. The public endpoint evaluates possession of a valid capability. This difference is reflected in both the URL namespace and URL configuration.

## Expected Consumers

Primary consumers are:

- authenticated trip owners requesting itinerary PDFs;
- authenticated trip owners creating and revoking share links;
- external recipients accessing valid shared itineraries;
- administrative operators inspecting persisted share-link state.

Future frontend, sharing, or notification components should consume this capability boundary rather than bypassing it.

## Architectural Boundaries

The implementation preserves the following boundaries:

- persistence is limited to share-link state;
- generated PDFs remain ephemeral;
- public serializers define an explicit safe representation;
- token validation is centralized;
- ownership remains enforced on authenticated operations;
- public access is isolated under a dedicated public URL namespace.

These boundaries allow document functionality to evolve without coupling document generation, authentication, and trip ownership into a single component.

