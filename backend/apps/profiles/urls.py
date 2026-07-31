"""
URL configuration for the Profiles application.
"""

from django.urls import path

from apps.profiles.views import ProfileMeView

app_name = "profiles"

urlpatterns = [
    path(
        "me/",
        ProfileMeView.as_view(),
        name="me",
    ),
]