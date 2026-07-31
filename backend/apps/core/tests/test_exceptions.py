"""
Tests for the shared application exception hierarchy.
"""

from django.test import SimpleTestCase

from apps.core.exceptions import (
    ApplicationError,
    BusinessRuleViolation,
    ExternalServiceError,
    ResourceNotOwned,
)


class ApplicationErrorTests(SimpleTestCase):
    """
    Tests for the base application exception.
    """

    def test_default_values(self):
        error = ApplicationError()

        self.assertEqual(
            error.message,
            "An application error occurred.",
        )

        self.assertEqual(
            error.code,
            "application_error",
        )

    def test_custom_values(self):
        error = ApplicationError(
            message="Custom error",
            code="custom_code",
        )

        self.assertEqual(error.message, "Custom error")
        self.assertEqual(error.code, "custom_code")


class BusinessRuleViolationTests(SimpleTestCase):

    def test_inheritance(self):
        error = BusinessRuleViolation()

        self.assertIsInstance(
            error,
            ApplicationError,
        )

        self.assertEqual(
            error.code,
            "business_rule_violation",
        )


class ResourceNotOwnedTests(SimpleTestCase):

    def test_inheritance(self):
        error = ResourceNotOwned()

        self.assertIsInstance(
            error,
            ApplicationError,
        )

        self.assertEqual(
            error.code,
            "resource_not_owned",
        )


class ExternalServiceErrorTests(SimpleTestCase):

    def test_inheritance(self):
        error = ExternalServiceError()

        self.assertIsInstance(
            error,
            ApplicationError,
        )

        self.assertEqual(
            error.code,
            "external_service_error",
        )