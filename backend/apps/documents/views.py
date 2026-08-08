from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents import services
from apps.documents.models import Document
from apps.documents.selectors import get_active_document_by_token
from apps.documents.serializers import (
    PublicItinerarySerializer,
    ShareLinkSerializer,
)
from apps.itinerary.selectors import get_trip_itinerary
from apps.trips.models import Trip


class GenerateItineraryPDFView(APIView):
    """
    Generate and return the authenticated owner's trip itinerary PDF.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get(
        self,
        request,
        pk,
    ):
        trip = get_object_or_404(
            Trip,
            pk=pk,
            user=request.user,
        )

        return services.generate_itinerary_pdf(
            trip=trip,
        )


class CreateShareLinkView(APIView):
    """
    Create a shareable document link for the authenticated
    owner of a trip.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(
        self,
        request,
        pk,
    ):
        trip = get_object_or_404(
            Trip,
            pk=pk,
            user=request.user,
        )

        document = services.create_share_link(
            trip=trip,
        )

        return Response(
            ShareLinkSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class RevokeShareLinkView(APIView):
    """
    Revoke a shareable document link belonging to the
    authenticated owner of a trip.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(
        self,
        request,
        pk,
        document_id,
    ):
        trip = get_object_or_404(
            Trip,
            pk=pk,
            user=request.user,
        )

        document = get_object_or_404(
            Document,
            pk=document_id,
            trip=trip,
        )

        updated = services.revoke_share_link(
            document=document,
        )

        return Response(
            ShareLinkSerializer(updated).data,
            status=status.HTTP_200_OK,
        )


class PublicSharedItineraryView(APIView):
    """
    Public shared itinerary endpoint.

    This is deliberately unauthenticated. The share token
    itself is the capability required to access the itinerary.
    """

    permission_classes = (
        permissions.AllowAny,
    )

    def get(
        self,
        request,
        token,
    ):
        document = get_active_document_by_token(
            token=token,
        )

        if document is None:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
            )

        trip = document.trip

        days = get_trip_itinerary(
            trip=trip,
        )

        payload = {
            "trip_title": trip.title,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "days": days,
        }

        serializer = PublicItinerarySerializer(
            payload,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )