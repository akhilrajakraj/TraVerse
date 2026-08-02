"""
URL configuration for the Recommendations application.
"""

from django.urls import path

from apps.recommendations.views import (
    RecommendationAcceptView,
    RecommendationRejectView,
    TripRecommendationsView,
)

app_name = "recommendations"

urlpatterns = [
    path(
        "trips/<uuid:trip_id>/recommendations/",
        TripRecommendationsView.as_view(),
        name="trip-recommendations",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/accept/",
        RecommendationAcceptView.as_view(),
        name="recommendation-accept",
    ),
    path(
        "recommendations/<uuid:recommendation_id>/reject/",
        RecommendationRejectView.as_view(),
        name="recommendation-reject",
    ),
]