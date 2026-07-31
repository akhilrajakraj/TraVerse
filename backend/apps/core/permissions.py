"""
Shared DRF permission classes.

App-specific permissions should live inside their respective applications.
This module contains only generic, reusable permissions.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """
    Object-level permission allowing only the owner of an object
    to access or modify it.

    Assumes the model exposes a `user_id` field.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        return getattr(obj, "user_id", None) == request.user.id


class IsStaffOrReadOnly(BasePermission):
    """
    Authenticated users may read.

    Only staff users may create, update or delete.
    """

    def has_permission(self, request, view) -> bool:

        if request.method in SAFE_METHODS:
            return bool(
                request.user and
                request.user.is_authenticated
            )

        return bool(
            request.user and
            request.user.is_staff
        )