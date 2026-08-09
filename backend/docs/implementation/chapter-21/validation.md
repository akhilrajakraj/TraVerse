Chapter 21 — documents App — Validation

Volume 6: Supporting Apps | Chapter 21 of 29

1. Validation Objective

Validation must establish that the current documents implementation works across:

model behavior,

share-link services,

selector rules,

PDF generation,

authenticated ownership,

public capability access,

revocation,

expiration,

complete integration flow.

This document reports what the repository's current test suite is designed to prove.

2. Repository Test Layout

Current test files:

backend/apps/documents/tests/
├── test_integration.py
├── test_selectors.py
├── test_services.py
└── test_views.py

fileciteturn139file0L1-L10

3. Model-Level Validation

The current implementation validates model semantics indirectly through service and selector workflows.

Important invariants:

Token exists

A newly created Document receives a share token automatically.

Token is independent

The share token is not the UUID primary key.

Active by default

A newly created link is active.

Expiration is optional

A link without an expiration remains valid while active.

Expiration invalidates access

A past expires_at causes is_valid to become false.

These behaviors are exercised through the selector and integration tests.

4. Selector Validation

test_selectors.py verifies five critical cases:

Scenario

Expected

Active token

Document returned

Unknown token

None

Revoked document

None

Expired document

None

Future expiration

Document returned

The repository explicitly contains these cases. fileciteturn142file0L2-L2

This establishes the selector as the security-sensitive lookup boundary.

5. Service Validation

test_services.py verifies share-link creation.

The test confirms:

correct trip association,

active state,

expiration preservation,

token existence,

token length.

The current test expects a 43-character URL-safe token for token_urlsafe(32). fileciteturn141file0L2-L2

6. Revocation Validation

The service test creates a document, revokes it, reloads it from the database, and confirms:

is_active == False

This proves revocation is persisted rather than merely changed in memory. fileciteturn141file0L2-L2

7. PDF Validation

The current service test validates:

HTTP 200
Content-Type = application/pdf
Content-Disposition contains attachment
filename contains Test Trip-itinerary.pdf
body starts with %PDF

This is stronger than testing only that a Python function returns bytes.

It verifies the HTTP artifact boundary as well. fileciteturn141file0L2-L2

8. PDF Generation Architecture Validation

The current service test mocks:

get_trip_itinerary()
ItineraryDaySerializer

and verifies that the generated response is still a valid PDF.

This isolates the PDF formatting responsibility from itinerary data retrieval.

The integration suite separately covers the broader application path.

9. Authentication Validation

The view tests verify that share-link creation requires authentication.

Expected:

unauthenticated POST
        ↓
401 Unauthorized

fileciteturn143file0L2-L2

10. Ownership Validation

The authenticated endpoints must enforce:

request.user == trip.user

The test suite verifies that a user cannot:

create a share link for another user's trip,

revoke another user's document,

generate another user's PDF.

Cross-user access returns:

404 Not Found

This is explicitly tested in test_views.py. fileciteturn143file0L2-L2

11. Public Access Validation

The public endpoint must work without authentication.

The test creates a valid document, removes authentication, requests the public URL, and expects:

200 OK

with:

trip_title
start_date
end_date
days

fileciteturn143file0L2-L2

12. Public Data-Surface Validation

The response is serialized through PublicItinerarySerializer.

The current serializer exposes:

trip_title
start_date
end_date
days

and no broad authenticated trip representation. fileciteturn133file0L2-L2

This establishes the intended public data boundary.

13. Invalid Token Validation

A completely unknown token must return:

404 Not Found

The view test explicitly verifies this. fileciteturn143file0L2-L2

14. Revoked Token Validation

A document created with:

is_active=False

must be unavailable publicly.

Expected:

404 Not Found

The view test explicitly verifies this. fileciteturn143file0L2-L2

15. Expired Token Validation

A document whose expiration is in the past must be unavailable publicly.

Expected:

404 Not Found

The view test explicitly verifies this. fileciteturn143file0L2-L2

16. End-to-End Share Workflow

The integration test validates the complete workflow:

Owner authentication
        ↓
POST create-share-link
        ↓
Document persisted
        ↓
share_token obtained
        ↓
Authentication removed
        ↓
GET public share URL
        ↓
200 OK
        ↓
Itinerary returned

This test demonstrates that the feature is not merely a collection of isolated units. fileciteturn140file0L2-L2

17. End-to-End Revocation Workflow

The integration test also verifies:

create link
    ↓
revoke link
    ↓
confirm is_active=False
    ↓
remove authentication
    ↓
request public URL
    ↓
404

This proves that the security control survives the full application boundary. fileciteturn140file0L2-L2

18. End-to-End Expiration Workflow

The integration suite creates an already-expired document and confirms the public endpoint rejects it.

This validates:

database expiration state
        ↓
model validity
        ↓
selector
        ↓
public view
        ↓
404

fileciteturn140file0L2-L2

19. Verification Command

The repository's documented test command is:

docker compose exec web python manage.py test apps.documents -v 2

For broader regression coverage, the project can also run its complete test suite.

20. Validation Matrix

Area

Validation

Token generation

Service tests

Token lookup

Selector tests

Revocation

Service + view + integration tests

Expiration

Selector + view + integration tests

PDF response

Service + view tests

Authentication

View tests

Ownership

View + integration tests

Public access

View + integration tests

Public field boundary

Serializer/view behavior

Complete workflow

Integration tests

Migration

Django migration state

ReportLab dependency

Requirements/runtime

21. Current-State Verification Notes

The current repository differs from the original Chapter 21 draft in several implementation details.

The current implementation should therefore be validated using the current paths and class names:

GenerateItineraryPDFView
CreateShareLinkView
RevokeShareLinkView
PublicSharedItineraryView

and:

/api/documents/
/api/v1/public/

The current URL configuration confirms these mounts. fileciteturn137file0L2-L2

22. Validation Boundary

The available repository evidence establishes strong automated coverage of:

link creation,

link validity,

link revocation,

expiration,

PDF generation,

ownership,

public access,

complete workflows.

It does not, from the inspected source alone, establish a numerical "all tests passed" result for the current repository checkout.

Therefore this documentation intentionally does not invent a pass count.

A current runtime test execution should be treated as the final release gate.

23. Final Acceptance Checklist

Document model exists.

UUID resource identity is separate from share capability.

Share tokens use secrets.token_urlsafe(32).

Share links can be revoked.

Expiration is represented and enforced.

PDF generation is in-memory.

ReportLab is pinned in requirements.

Authenticated PDF generation checks ownership.

Authenticated share-link creation checks ownership.

Authenticated revocation checks ownership.

Public access requires no authentication.

Public route uses <str:token>.

Unknown tokens return 404.

Revoked tokens return 404.

Expired tokens return 404.

Public serializer is deliberately minimal.

Selector tests cover active/unknown/revoked/expired/future cases.

Service tests cover PDF output and link lifecycle.

View tests cover security boundaries.

Integration tests cover the complete workflow.

A fresh runtime execution of the full test command has been performed for this documentation release.

A Git commit for this documentation release has been per