Chapter 21 — documents App — Lessons Learned

Volume 6: Supporting Apps | Chapter 21 of 29

1. A Generated Artifact Does Not Automatically Need Persistence

The PDF is a representation of database state.

Persisting it would create another artifact that could become stale whenever:

the itinerary changes,

an AI run regenerates the itinerary,

an itinerary item is edited.

The current implementation instead generates the PDF from the current itinerary each time. fileciteturn131file0L2-L2

The broader lesson is:

Persist durable domain state; generate cheap representations when the representation can safely be recreated.

2. Resource Identity and Access Capability Are Different Concepts

Document.id answers:

Which database resource is this?

share_token answers:

What secret grants access to this public representation?

Those questions should not be represented by the same value.

The current model therefore keeps both values separate. fileciteturn130file0L2-L2

This separation remains valuable even when both values appear difficult to guess.

3. Security Requirements Should Determine the Primitive

The repository uses:

secrets.token_urlsafe(32)

rather than another UUID.

The important lesson is not simply "use secrets."

The deeper lesson is:

Select an API according to the security property it is designed to provide, not merely because its output happens to look sufficiently random.

4. Public Does Not Mean Permissionless Data

The public endpoint is intentionally unauthenticated.

That does not make the response unrestricted.

The safe architecture is:

No authentication
        +
unguessable capability
        +
minimal response serializer
        +
revocation
        +
expiration validation

The public serializer is an explicit allow-list. fileciteturn133file0L2-L2

5. Different Security Models Deserve Different URL Structures

The project separates:

/api/documents/

from:

/api/v1/public/

This makes the different security model visible at the routing level. fileciteturn137file0L2-L2

A public capability endpoint hidden among authenticated resource routes would be easier to misunderstand and accidentally harden incorrectly later.

6. Revocation Is More Useful Than Destructive Deletion for Capabilities

A share link is an authorization capability.

Revoking it with:

is_active = False

provides immediate invalidation while retaining:

creation history,

ownership association,

timestamps,

the ability to audit the link's existence.

This is more useful than deleting the record simply to disable access.

7. A Business Rule Belongs at a Stable Boundary

Document.is_valid centralizes:

active state,

expiration.

The selector then applies that rule when resolving public access.

This is safer than making the public view independently check:

is_active

and:

expires_at

in its own custom way.

8. Selectors Protect Query Semantics

The public view does not perform a raw document lookup.

It calls:

get_active_document_by_token()

That selector owns the meaning of "active share link."

This keeps the security-sensitive lookup rule reusable and testable. fileciteturn134file0L2-L2

9. Existing Query Discipline Should Continue into Public Endpoints

The public endpoint reuses:

get_trip_itinerary()

rather than creating a second itinerary query implementation.

The lesson is important:

Public endpoints should not become exceptions to established performance and data-access discipline.

A public endpoint can receive less predictable traffic than an authenticated workflow, making query efficiency more important rather than less important.

10. Authentication and Capability Authorization Are Not the Same Thing

Authenticated endpoints establish:

identity → ownership → authorization

The public share endpoint establishes:

possession of valid capability → authorization

Both are authorization models.

They simply answer different questions.

11. 404 Can Be the Correct Public Security Boundary

The public endpoint returns 404 for:

unknown token,

revoked token,

expired token.

The requester has no authenticated identity against which ownership can be evaluated.

Treating an unusable capability as unavailable avoids exposing unnecessary information about whether a resource once existed.

The current implementation intentionally follows this rule. fileciteturn132file0L2-L2

12. FileResponse Is an Appropriate Boundary for Downloadable Content

The current service returns a Django FileResponse instead of forcing the view to manually construct the file response.

This keeps the service responsible for the artifact and allows the view to remain responsible for request authorization.

The tests verify:

status,

MIME type,

attachment disposition,

actual PDF bytes. fileciteturn141file0L2-L2

13. A PDF Is an Output Format, Not a Domain Model

The Document model does not contain:

pdf_file
pdf_blob
generated_pdf

It represents the share-link capability.

This distinction prevents the app name from dictating the data model.

14. Integration Tests Are Especially Valuable for Security Workflows

A unit test can prove:

selector rejects expired token

A view test can prove:

endpoint returns 404

But an integration test proves the complete behavior:

owner creates link
 → token is persisted
 → authentication is removed
 → public endpoint receives token
 → itinerary is returned

The current integration suite explicitly exercises that chain. fileciteturn140file0L2-L2

15. Current Code Must Override Historical Documentation

The original Chapter 21 draft described an earlier implementation.

The current repository has since changed:

route names,

URL prefixes,

PDF implementation,

view names,

test organization,

dependency declarations.

Therefore documentation must be reconciled against the current code before being treated as authoritative.

The current repository's documents commit history includes a later documentation commit, while the implementation itself has continued to evolve. fileciteturn146file0L2-L2

The engineering lesson is:

Documentation is part of the system, but source code remains the authority for current implementation state.

16. Capability Expiration Is Supported Below the HTTP Creation Layer

The model and service support:

expires_at

and the selector enforces it.

However, the current create-link view does not expose a request parameter for expiration.

This is an important distinction between:

domain capability

and:

current API surface

Documentation should preserve that distinction rather than claiming a feature exists simply because the model can represent it.

17. Admin Presence Should Not Be Assumed from App Presence

The app has an admin.py, but the current file contains only the scaffold placeholder. fileciteturn150file0L1-L2

Therefore:

Django app exists
≠
admin interface exists

This is a useful reminder to verify actual registrations rather than inferring features from filenames.

18. Security Boundaries Should Be Obvious in Code

Several choices reinforce one another:

public_urls.py
      +
AllowAny
      +
<str:token>
      +
get_active_document_by_token()
      +
PublicItinerarySerializer

Each piece communicates that the public endpoint is intentionally different.

The lesson is architectural readability:

Security-sensitive behavior should be visible through structure, not hidden in a few scattered conditions.

19. Regression Tests Protect Earlier Architecture

The document app depends on itinerary behavior established earlier.

Its tests therefore verify integration with the existing itinerary selector instead of replacing it.

This reduces the chance that the new document feature silently introduces a second, inconsistent interpretation of itinerary data.

20. Conclusion

Chapter 21 establishes a reusable pattern for TraVerse:

Durable domain state
        ↓
Reusable selector/service
        ↓
Generated representation

and, for public sharing:

Authenticated owner
        ↓
Capability creation
        ↓
Unpredictable token
        ↓
Public endpoint
        ↓
Minimal representation
        ↓
Revocation / expiration

The most important lesson is not PDF generation itself.

It is the disciplined separation of:

identity,

ownership,

capability,

representation,

persistence,

and public exposure.