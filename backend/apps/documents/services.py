from datetime import datetime
from io import BytesIO

from django.http import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.core.services import log_audit_event
from apps.documents.models import Document
from apps.itinerary.selectors import get_trip_itinerary
from apps.itinerary.serializers import ItineraryDaySerializer
from apps.trips.models import Trip


def create_share_link(
    *,
    trip: Trip,
    expires_at: datetime | None = None,
    actor=None,
) -> Document:
    """Create a shareable document link and record who created it."""
    document = Document.objects.create(
        trip=trip,
        expires_at=expires_at,
    )
    log_audit_event(
        user=actor,
        action="share_link_created",
        metadata={
            "trip_id": str(trip.id),
            "document_id": str(document.id),
        },
    )
    return document


def revoke_share_link(*, document: Document, actor=None) -> Document:
    """Revoke an active shareable document link and audit the action."""
    document.is_active = False
    document.save(update_fields=["is_active", "updated_at"])
    log_audit_event(
        user=actor,
        action="share_link_revoked",
        metadata={"document_id": str(document.id)},
    )
    return document


def generate_itinerary_pdf(*, trip: Trip) -> FileResponse:
    """Generate the trip itinerary PDF in memory."""
    days = get_trip_itinerary(trip=trip)
    serialized_days = ItineraryDaySerializer(days, many=True).data

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setTitle(f"{trip.title} - Itinerary")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, trip.title)
    y -= 30
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"{trip.start_date} to {trip.end_date}")
    y -= 35

    for day in serialized_days:
        if y < 80:
            pdf.showPage()
            y = height - 50

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Day {day['day_number']} — {day['date']}")
        y -= 20

        if day.get("summary"):
            pdf.setFont("Helvetica", 10)
            pdf.drawString(60, y, str(day["summary"])[:100])
            y -= 20

        for item in day.get("items", []):
            if y < 100:
                pdf.showPage()
                y = height - 50

            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(60, y, str(item["title"])[:90])
            y -= 16
            pdf.setFont("Helvetica", 9)

            if item.get("start_time"):
                pdf.drawString(70, y, f"Time: {item['start_time']}")
                y -= 14
            if item.get("description"):
                pdf.drawString(70, y, str(item["description"])[:100])
                y -= 14
            if item.get("estimated_cost_usd") is not None:
                pdf.drawString(70, y, f"Estimated cost: ${item['estimated_cost_usd']}")
                y -= 14

            destination = item.get("destination")
            if destination and destination.get("name"):
                pdf.drawString(70, y, f"Destination: {destination['name']}")
                y -= 14
            y -= 8

    pdf.save()
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"{trip.title}-itinerary.pdf",
        content_type="application/pdf",
    )
