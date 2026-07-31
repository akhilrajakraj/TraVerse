"""
Views for the Profiles application.
"""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.profiles.serializers import ProfileSerializer


class ProfileMeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve and update the authenticated user's profile.
    """

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self):
        """
        Return the authenticated user's profile.
        """

        return self.request.user.profile