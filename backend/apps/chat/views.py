"""
API views for conversational chat.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.services import generate_chat_reply
from apps.chat.serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
)
from apps.chat.services import ChatService
from apps.trips.models import Trip


class ChatAPIView(APIView):
    """
    Conversational AI endpoint.
    """

    permission_classes = (
        IsAuthenticated,
    )

    def post(
        self,
        request,
        trip_id,
    ):
        """
        Send a user message to the conversational AI.
        """

        serializer = ChatRequestSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        trip = get_object_or_404(
            Trip,
            id=trip_id,
            user=request.user,
        )

        assistant_message = generate_chat_reply(
            trip=trip,
            user_message=serializer.validated_data[
                "message"
            ],
        )

        session = ChatService.get_or_create_active_session(
            trip=trip,
        )

        response = ChatResponseSerializer(
            {
                "session_id": session.id,
                "assistant_message": assistant_message,
                "created_at": session.updated_at,
            }
        )

        return Response(
            response.data,
            status=status.HTTP_200_OK,
        )