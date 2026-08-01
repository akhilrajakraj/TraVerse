"""
Custom exceptions for the Trips application.

These exceptions represent business rule violations raised by the
Trips service layer. They remain independent of Django REST Framework
and are translated into API responses by the project's centralized
exception handling infrastructure.
"""

from apps.core.exceptions import BusinessRuleViolation


class InvalidDateRange(BusinessRuleViolation):
    """
    Raised when a trip's end date precedes its start date.
    """

    default_message = (
        "Trip end date must be on or after the start date."
    )

    default_code = "invalid_date_range"


class InvalidStatusTransition(BusinessRuleViolation):
    """
    Raised when a trip attempts an invalid lifecycle transition.
    """

    default_message = (
        "This status change is not allowed from the trip's current status."
    )

    default_code = "invalid_status_transition"