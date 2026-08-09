from django.shortcuts import get_object_or_404

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents import services
from apps.documents.caching import get_cached_active_document
from apps.documents.models import Document
from apps.documents.serializers import PublicItinerarySerializer, ShareLinkSerializer
from apps.itinerary.selectors import get_trip_itinerary
from apps.trips.models import Trip


class GenerateItineraryPDFView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk, user=request.user)
        return services.generate_itinerary_pdf(trip=trip)


class CreateShareLinkView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk, user=request.user)
        document = services.create_share_link(
            trip=trip,
            actor=request.user,
        )
        return Response(
            ShareLinkSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class RevokeShareLinkView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk, document_id):
        trip = get_object_or_404(Trip, pk=pk, user=request.user)
        document = get_object_or_404(Document, pk=document_id, trip=trip)
        updated = services.revoke_share_link(
            document=document,
            actor=request.user,
        )
        return Response(
            ShareLinkSerializer(updated).data,
            status=status.HTTP_200_OK,
        )


class PublicSharedItineraryView(APIView):
    """Public shared itinerary endpoint; the share token is the capability."""

    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        document = get_cached_active_document(token=token)
        if document is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        trip = document.trip
        days = get_trip_itinerary(trip=trip)
        payload = {
            "trip_title": trip.title,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "days": days,
        }
        return Response(
            PublicItinerarySerializer(payload).data,
            status=status.HTTP_200_OK,
        )
