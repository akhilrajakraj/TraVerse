"""
URL configuration for the Itinerary application.
"""

from django.urls import path

from apps.itinerary.views import (
    AddItineraryItemView,
    TripItineraryView,
)

app_name = "itinerary"

urlpatterns = [
    path(
        "trips/<uuid:trip_id>/itinerary/",
        TripItineraryView.as_view(),
        name="trip-itinerary",
    ),
    path(
        "itinerary-days/<uuid:day_id>/items/",
        AddItineraryItemView.as_view(),
        name="add-itinerary-item",
    ),
]