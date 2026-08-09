"""
API views for the Notifications application.

This module exposes the authenticated read-facing notification API.

Business logic remains in the service layer:
    - services.mark_as_read()

The views are responsible only for:
    - authentication
    - request parsing
    - queryset scoping
    - object lookup
    - serializer/response handling
"""

from django.shortcuts import get_object_or_404

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(ListAPIView):
    """
    Return notifications belonging to the authenticated user.

    By default, all notifications belonging to the current user are
    returned.

    Optional query parameter:

        ?unread=true

    When supplied, only unread notifications are returned.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return only notifications owned by the authenticated user.

        The ownership restriction is applied at the queryset level so
        notifications belonging to other users can never enter the
        response queryset.
        """

        queryset = Notification.objects.filter(
            user=self.request.user,
        )

        unread_only = self.request.query_params.get("unread") == "true"

        if unread_only:
            queryset = queryset.filter(
                is_read=False,
            )

        return queryset


class NotificationMarkReadView(APIView):
    """
    Mark one notification as read.

    The notification must belong to the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_pk):
        """
        Mark the requested notification as read and return its
        serialized representation.
        """

        notification = get_object_or_404(
            Notification,
            pk=notification_pk,
            user=request.user,
        )

        updated = services.mark_as_read(
            notification=notification,
        )

        return Response(
            NotificationSerializer(updated).data,
        )