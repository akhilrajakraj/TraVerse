"""
Permission classes for the Trips application.
"""

from apps.core.permissions import IsOwner


class IsTripOwner(IsOwner):
    """
    Object-level permission ensuring that users can only
    access or modify their own trips.
    """

    pass