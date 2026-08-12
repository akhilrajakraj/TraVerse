"""
API views for the Recommendations application.
"""

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recommendations.models import Recommendation
from apps.recommendations.selectors import get_trip_recommendations
from apps.recommendations.serializers import RecommendationSerializer
from apps.recommendations.services import (
    accept_recommendation,
    reject_recommendation,
)
from apps.trips.models import Trip


class TripRecommendationsView(APIView):
    """Retrieve recommendations belonging to a trip owned by the user."""

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        trip_id,
    ):
        trip = get_object_or_404(
            Trip,
            id=trip_id,
            user=request.user,
        )

        recommendations = get_trip_recommendations(trip)
        status_filter = request.query_params.get("status")

        if status_filter:
            recommendations = recommendations.filter(
                status=status_filter,
            )

        serializer = RecommendationSerializer(
            recommendations,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class RecommendationAcceptView(APIView):
    """Accept a recommendation owned by the authenticated user."""

    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        recommendation_id,
    ):
        recommendation = get_object_or_404(
            Recommendation.objects.select_related("trip"),
            id=recommendation_id,
            trip__user=request.user,
        )

        recommendation = accept_recommendation(recommendation)
        serializer = RecommendationSerializer(recommendation)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class RecommendationRejectView(APIView):
    """Reject a recommendation owned by the authenticated user."""

    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        recommendation_id,
    ):
        recommendation = get_object_or_404(
            Recommendation.objects.select_related("trip"),
            id=recommendation_id,
            trip__user=request.user,
        )

        recommendation = reject_recommendation(recommendation)
        serializer = RecommendationSerializer(recommendation)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
