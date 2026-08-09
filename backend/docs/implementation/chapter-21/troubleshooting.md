Chapter 21 — documents App — Troubleshooting

Volume 6: Supporting Apps | Chapter 21 of 29

1. Public Share Link Returns 404

Symptom

A newly generated share URL returns:

404 Not Found

Likely causes

token was copied incorrectly,

document was revoked,

document has expired,

public route is not mounted,

wrong URL converter is being used.

Verification

The public route must ultimately resolve to:

/api/v1/public/share/<str:token>/

The current repository uses <str:token>. fileciteturn136file0L1-L2

Inspect the document:

docker compose exec web python manage.py shell -c "
from apps.documents.models import Document
d = Document.objects.first()
print(d.id)
print(d.share_token)
print(d.is_active)
print(d.expires_at)
print(d.is_valid)
"

2. Revoked Link Still Appears Valid

Symptom

A link was revoked but the public endpoint still appears to find the document.

Correct behavior

Revocation sets:

is_active = False

The selector explicitly filters active documents and then validates the model. fileciteturn134file0L2-L2

Verify:

docker compose exec web python manage.py shell -c "
from apps.documents.models import Document
d = Document.objects.first()
print('active:', d.is_active)
print('valid:', d.is_valid)
"

If is_active is False, the public endpoint should return 404.

3. Expired Link Still Works

Symptom

A link has an expires_at in the past but remains accessible.

Cause to inspect

The public path must use:

get_active_document_by_token()

rather than a raw:

Document.objects.get(share_token=token)

The selector checks both active state and expiration validity. fileciteturn134file0L2-L2

4. PDF Is Not Returned

Symptom

The PDF endpoint fails or returns an unexpected response.

Check

The current service returns a Django FileResponse with:

Content-Type: application/pdf

and an attachment filename.

The service test explicitly validates both the content type and %PDF magic number. fileciteturn141file0L2-L2

Inspect ReportLab:

docker compose exec web python -c "import reportlab; print(reportlab.Version)"

The repository pins:

reportlab==4.4.3

fileciteturn145file0L2-L2

5. PDF Is Empty or Corrupted

Check the generation order

The current service:

BytesIO
 ↓
canvas.Canvas(...)
 ↓
write content
 ↓
pdf.save()
 ↓
buffer.seek(0)
 ↓
FileResponse

The pdf.save() call must occur before the response reads the buffer. fileciteturn131file0L2-L2

The service test confirms the response body begins with:

%PDF

fileciteturn141file0L2-L2

6. PDF Contains Unexpectedly Stale Itinerary Data

The implementation intentionally regenerates the PDF from the current itinerary.

The service calls:

get_trip_itinerary(trip=trip)

before constructing the PDF. fileciteturn131file0L2-L2

Therefore a previously downloaded PDF is a snapshot, but a new request should represent the current database state.

There is no stored PDF artifact to update.

7. Another User Receives Access

Symptom

An authenticated user can access another user's trip document.

Expected behavior

Authenticated document views retrieve trips using:

Trip(pk=..., user=request.user)

The view tests explicitly verify cross-user access returns 404 for PDF generation and share-link creation. fileciteturn143file0L2-L2

The revoke view also verifies the document belongs to the already-owned trip.

8. Public Endpoint Requires Authentication

Symptom

A valid public share link returns 401.

Check

PublicSharedItineraryView must use:

permission_classes = (
    permissions.AllowAny,
)

The current repository does exactly this. fileciteturn132file0L2-L2

Do not "fix" the problem by adding authentication to the public endpoint. The token is intentionally the capability.

9. Public Endpoint Exposes Too Much Data

Risk

Replacing PublicItinerarySerializer with a broad authenticated serializer.

Correct design

The public serializer explicitly contains only:

trip_title
start_date
end_date
days

fileciteturn133file0L2-L2

Any expansion of this serializer should be treated as a security-sensitive change.

10. Wrong URL Prefix

The current repository does not use the earlier draft's /api/v1/trips/ document prefix.

Current authenticated mount:

/api/documents/

Current public mount:

/api/v1/public/

This is visible in the current root URL configuration. fileciteturn137file0L2-L2

11. Token Looks Different from the Document ID

This is expected.

Example conceptual shape:

id:
UUID-shaped identifier

share_token:
URL-safe security token

The model deliberately generates the latter with secrets.token_urlsafe(32). fileciteturn130file0L2-L2

12. Migration Problems

Verify migration state:

docker compose exec web python manage.py showmigrations documents

The repository contains:

documents/
└── 0001_initial.py

The migration depends on:

trips.0002_packingitem

fileciteturn144file0L2-L2

13. ReportLab Import Error

Symptom

ModuleNotFoundError: No module named 'reportlab'

Cause

The dependency is missing from the runtime environment.

The repository declares:

reportlab==4.4.3

in requirements/base.txt. fileciteturn145file0L2-L2

After rebuilding the application environment, verify:

docker compose exec web python -c "import reportlab; print(reportlab.Version)"

14. Debugging the Selector

docker compose exec web python manage.py shell -c "
from apps.documents.models import Document
from apps.documents.selectors import get_active_document_by_token

d = Document.objects.first()

print('token:', d.share_token)
print('valid:', d.is_valid)
print('selector result:', get_active_document_by_token(token=d.share_token))
"

Expected:

valid: True
selector result: <Document ...>

For revoked or expired links:

selector result: None

15. Debugging the Full Workflow

The repository's integration test already models the intended sequence:

authenticate as owner
 ↓
create share link
 ↓
retrieve Document
 ↓
remove authentication
 ↓
access public URL
 ↓
verify itinerary response

The same workflow is then tested for revocation and expiration. fileciteturn140file0L2-L2

16. Recovery Strategy

The documents app has a deliberately small rollback surface.

Compromised link

Revoke it:

is_active = False

Expired link

No data deletion is required.

Broken PDF generation

The failure affects the requested artifact response, not the underlying trip/itinerary data.

Public serializer mistake

Restore the minimal allow-listed field set before re-enabling public access.

17. Important Non-Implemented Areas

The current repository does not establish:

persisted PDF files,

cloud object storage,

document version history,

document admin registration,

automated public-link expiration cleanup,

a configurable expiration value on the current HTTP create-link endpoint.

The model/service support expires_at, but the current CreateShareLinkView calls create_share_link(trip=trip) without passing an expiration supplied by the request. fileciteturn131file0L2-L2 fileciteturn132file0L2-L2

These should not be documented as completed functionality.