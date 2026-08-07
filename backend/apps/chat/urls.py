"""
URL configuration for the chat application.
"""

from __future__ import annotations

from django.urls import path

from apps.chat.views import ChatAPIView


app_name = "chat"


urlpatterns = [
    path(
        "trips/<uuid:trip_id>/chat/",
        ChatAPIView.as_view(),
        name="chat",
    ),
]