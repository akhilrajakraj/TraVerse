from django.contrib import admin

from apps.bookings.models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "booking_type",
        "status",
        "trip",
        "estimated_cost",
        "created_at",
    )
    list_filter = ("booking_type", "status")
    search_fields = (
        "title",
        "trip__title",
        "trip__user__email",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
