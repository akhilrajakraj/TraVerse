"""
Tests for shared abstract base models.
"""

from django.test import SimpleTestCase

from apps.core.models import (
    SoftDeleteModel,
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class AbstractModelTests(SimpleTestCase):
    """
    Verify that shared models remain abstract.
    """

    def test_timestamp_model_is_abstract(self):
        self.assertTrue(TimeStampedModel._meta.abstract)

    def test_uuid_model_is_abstract(self):
        self.assertTrue(UUIDPrimaryKeyModel._meta.abstract)

    def test_soft_delete_model_is_abstract(self):
        self.assertTrue(SoftDeleteModel._meta.abstract)