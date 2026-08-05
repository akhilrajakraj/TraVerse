"""
URL configuration for the Trips application.
"""

from django.urls import path

from apps.trips.views import (
    TripListCreateView,
    TripRetrieveUpdateDestroyView,
    TripStatusUpdateView,
    TripPackingListView,
)

app_name = "trips"

urlpatterns = [
    path(
        "",
        TripListCreateView.as_view(),
        name="trip-list",
    ),
    path(
        "<uuid:pk>/",
        TripRetrieveUpdateDestroyView.as_view(),
        name="trip-detail",
    ),
    path(
        "<uuid:pk>/status/",
        TripStatusUpdateView.as_view(),
        name="trip-status",
    ),
    path(
        "<uuid:pk>/packing/",
        TripPackingListView.as_view(),
        name="trip-packing-list",
    ),
]