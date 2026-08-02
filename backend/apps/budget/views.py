"""
API views for the Budget application.
"""

from django.shortcuts import get_object_or_404

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.budget import services
from apps.budget.models import Budget
from apps.budget.serializers import (
    BudgetLineItemSerializer,
    BudgetSerializer,
    CreateBudgetLineItemSerializer,
)
from apps.trips.models import Trip


class TripBudgetView(APIView):
    """
    Retrieve the budget for a trip owned by the
    authenticated user.
    """

    permission_classes = [
        permissions.IsAuthenticated,
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

        serializer = BudgetSerializer(
            trip.budget,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class BudgetLineItemCreateView(APIView):
    """
    Add a new budget line item.
    """

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(
        self,
        request,
        trip_id,
    ):
        trip = get_object_or_404(
            Trip,
            id=trip_id,
            user=request.user,
        )

        serializer = CreateBudgetLineItemSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        line_item = services.create_budget_line_item(
            budget=trip.budget,
            **serializer.validated_data,
        )

        response_serializer = BudgetLineItemSerializer(
            line_item,
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )