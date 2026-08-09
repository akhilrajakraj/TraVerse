from django.urls import path

from apps.bookings.views import TripBookingListCreateView

app_name = "bookings"

urlpatterns = [
    path(
        "<uuid:trip_pk>/bookings/",
        TripBookingListCreateView.as_view(),
        name="trip-booking-list-create",
    ),
]
