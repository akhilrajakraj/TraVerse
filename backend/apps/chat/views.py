"""API views for conversational chat."""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.services import generate_chat_reply
from apps.chat.serializers import ChatRequestSerializer, ChatResponseSerializer
from apps.chat.services import ChatService
from apps.core.rate_limiting import increment_rate_limit, is_rate_limited
from apps.trips.models import Trip


_CHAT_RATE_LIMIT_MAX = 30
_CHAT_RATE_LIMIT_WINDOW_SECONDS = 3600


class ChatAPIView(APIView):
    """Conversational AI endpoint."""

    permission_classes = (IsAuthenticated,)

    def post(self, request, trip_id):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip = get_object_or_404(Trip, id=trip_id, user=request.user)

        rate_limit_key = f"chat_message_rate_limit:{request.user.id}"
        if is_rate_limited(
            key=rate_limit_key,
            max_requests=_CHAT_RATE_LIMIT_MAX,
        ):
            return Response(
                {
                    "error": {
                        "code": "rate_limited",
                        "message": f"Maximum {_CHAT_RATE_LIMIT_MAX} messages per hour.",
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        increment_rate_limit(
            key=rate_limit_key,
            window_seconds=_CHAT_RATE_LIMIT_WINDOW_SECONDS,
        )

        assistant_message = generate_chat_reply(
            trip=trip,
            user_message=serializer.validated_data["message"],
        )

        session = ChatService.get_or_create_active_session(trip=trip)

        response = ChatResponseSerializer(
            {
                "session_id": session.id,
                "assistant_message": assistant_message,
                "created_at": session.updated_at,
            }
        )

        return Response(response.data, status=status.HTTP_200_OK)
