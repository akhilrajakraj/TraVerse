"""
URL configuration for the Destinations application.
"""

from django.urls import path

from apps.destinations.views import (
    DestinationDetailView,
    DestinationListView,
)

app_name = "destinations"

urlpatterns = [
    path(
        "",
        DestinationListView.as_view(),
        name="destination-list",
    ),
    path(
        "<uuid:pk>/",
        DestinationDetailView.as_view(),
        name="destination-detail",
    ),
]