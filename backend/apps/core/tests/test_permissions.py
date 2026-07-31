"""
Tests for shared DRF permission classes.
"""

from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.core.permissions import (
    IsOwner,
    IsStaffOrReadOnly,
)


class IsOwnerTests(SimpleTestCase):

    def setUp(self):
        self.permission = IsOwner()

    def test_owner_has_permission(self):
        request = SimpleNamespace(
            user=SimpleNamespace(id=1),
        )

        obj = SimpleNamespace(user_id=1)

        self.assertTrue(
            self.permission.has_object_permission(
                request,
                None,
                obj,
            )
        )

    def test_non_owner_denied(self):
        request = SimpleNamespace(
            user=SimpleNamespace(id=1),
        )

        obj = SimpleNamespace(user_id=2)

        self.assertFalse(
            self.permission.has_object_permission(
                request,
                None,
                obj,
            )
        )


class IsStaffOrReadOnlyTests(SimpleTestCase):

    def setUp(self):
        self.permission = IsStaffOrReadOnly()

    def test_authenticated_user_can_read(self):
        request = SimpleNamespace(
            method="GET",
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
            ),
        )

        self.assertTrue(
            self.permission.has_permission(
                request,
                None,
            )
        )

    def test_staff_can_write(self):
        request = SimpleNamespace(
            method="POST",
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=True,
            ),
        )

        self.assertTrue(
            self.permission.has_permission(
                request,
                None,
            )
        )

    def test_non_staff_cannot_write(self):
        request = SimpleNamespace(
            method="POST",
            user=SimpleNamespace(
                is_authenticated=True,
                is_staff=False,
            ),
        )

        self.assertFalse(
            self.permission.has_permission(
                request,
                None,
            )
        )