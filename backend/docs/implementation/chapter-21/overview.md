Chapter 21 — documents App

Volume 6: Supporting Apps | Chapter 21 of 29

The documents app introduces the project's first downloadable artifact and its first genuinely public, unauthenticated access path. The app does not store generated PDFs; instead, it persists revocable share-link capabilities and regenerates the itinerary PDF from current trip data when requested.

1. Purpose

The documents app provides two related capabilities:

Generate a current trip itinerary as a PDF.

Create a public share link through which an unauthenticated visitor can view a restricted itinerary representation.

The app therefore introduces two different security models:

Authenticated owner operations for PDF generation, share-link creation, and revocation.

Capability-token access for public itinerary sharing.

The current implementation keeps the generated PDF ephemeral. A Document row represents the share link, not the PDF file itself.

2. Learning Objective

By the end of this chapter, an engineer should understand:

Why generated documents do not always need to become persisted database/file artifacts.

Why a public capability token must be distinct from the resource primary key.

Why secrets.token_urlsafe() is appropriate for an access-granting token.

How ownership checks are preserved for authenticated operations.

How a deliberately public endpoint can be made safe through an explicit minimal serializer and capability token.

Why revoked and expired capabilities are treated as unavailable resources.

How selectors, services, serializers, and views divide responsibilities.

How the document workflow is verified from isolated service tests through end-to-end integration tests.

3. Domain Responsibilities

3.1 Share-link management

A Document records:

the owning trip,

a public capability token,

whether the link is active,

optional expiration,

timestamps.

The link can be revoked without deleting the database row.

3.2 PDF generation

The PDF is generated in memory using ReportLab.

The current service:

obtains the trip itinerary through the existing itinerary selector,

serializes itinerary days,

writes the content into an in-memory buffer,

creates an A4 PDF,

returns a Django FileResponse.

No PDF file is written to persistent storage.

3.3 Public itinerary access

A public visitor supplies the share token.

The selector:

looks up the token,

requires the link to be active,

validates expiration,

returns the document only when usable.

The public view then returns only:

trip title,

start date,

end date,

itinerary days.

The public serializer deliberately does not expose authenticated-only trip data such as budgets or agent execution history.

4. Current Architecture

Authenticated User
       │
       ├── GET /api/documents/trips/<uuid>/pdf/
       │       │
       │       └── GenerateItineraryPDFView
       │               │
       │               └── documents.services
       │                       │
       │                       ├── get_trip_itinerary()
       │                       ├── ItineraryDaySerializer
       │                       └── ReportLab → FileResponse
       │
       ├── POST /api/documents/trips/<uuid>/share-link/
       │       │
       │       └── CreateShareLinkView
       │               │
       │               └── create_share_link()
       │                       │
       │                       └── Document
       │
       └── POST /api/documents/trips/<uuid>/share-link/<uuid>/revoke/
               │
               └── RevokeShareLinkView
                       │
                       └── revoke_share_link()
                               │
                               └── is_active=False


Public Visitor
       │
       └── GET /api/v1/public/share/<token>/
               │
               └── PublicSharedItineraryView
                       │
                       └── get_active_document_by_token()
                               │
                               ├── token match
                               ├── is_active=True
                               └── expiration valid
                                       │
                                       └── get_trip_itinerary()
                                               │
                                               └── PublicItinerarySerializer

The current repository confirms that authenticated document routes are mounted under api/documents/, while the public URL configuration is mounted separately under api/v1/public/. The public route uses a string token rather than a UUID converter. fileciteturn135file0L1-L2 fileciteturn136file0L1-L2 fileciteturn137file0L2-L2

5. Core Design Principles

5.1 One source of truth

The database remains the authoritative source for itinerary information.

The PDF is a representation of that state, not a second persisted copy.

5.2 Identity and authorization are separate

Document.id identifies the database resource.

Document.share_token grants capability-based public access.

They deliberately serve different purposes.

5.3 Public does not mean unrestricted data

The public endpoint is unauthenticated, but the returned representation is intentionally restricted.

5.4 Revocation is state, not deletion

A link can be disabled by changing is_active.

This provides an immediate security control without requiring the resource itself to disappear.

5.5 Security-sensitive randomness uses the security-oriented primitive

The repository uses secrets.token_urlsafe(32) for the share token. fileciteturn130file0L2-L2

6. Important Current-Repository Note

The original Chapter 21 implementation document describes an earlier route shape and earlier PDF implementation. The current repository has evolved.

The current code:

mounts authenticated document URLs through api/documents/,

mounts public links through api/v1/public/,

names the PDF view GenerateItineraryPDFView,

returns a FileResponse,

uses ReportLab's low-level canvas API,

supports expires_at at the service/model level,

keeps admin.py unregistered at present.

This documentation follows the current repository implementation rather than reproducing outdated snippets.

7. Relationship to Previous Chapters

Chapter 3 — Core Foundations

Document uses the shared UUIDPrimaryKeyModel and TimeStampedModel.

Chapter 8 — Itinerary

The public endpoint and PDF generator reuse the existing get_trip_itinerary() selector rather than rebuilding itinerary queries.

Chapter 9 — Budget

Public sharing does not expose budget data.

Chapter 12+ — AI Agents

The document representation is independent of AgentRun history. Public sharing exposes the itinerary, not the internal AI execution record.

Chapter 21's architectural transition

This chapter begins Volume 6 and changes the project's output surface from authenticated JSON resources to generated artifacts and controlled public access.

8. Completion Definition

The chapter is complete when:

the document model and migration exist,

secure share tokens are generated automatically,

share links can be created and revoked,

optional expiration is respected,

authenticated users cannot operate on another user's trip,

PDFs are generated successfully,

public links work without authentication,

invalid/revoked/expired tokens return 404,

public responses remain deliberately minimal,

selector/service/view/integration tests cover the complete workflow,

and the implementation is documented against the repository's actual current state.