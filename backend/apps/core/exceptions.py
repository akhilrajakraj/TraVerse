"""
Base exception hierarchy for the application layer.

Views and serializers will translate these into consistent API responses.
Never raise a bare Exception from the application's service layer.
"""


class ApplicationError(Exception):
    """
    Base class for all expected application-level exceptions.
    """

    default_message = "An application error occurred."
    default_code = "application_error"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
    ):
        self.message = message or self.default_message
        self.code = code or self.default_code

        super().__init__(self.message)


class BusinessRuleViolation(ApplicationError):
    """
    Raised when an operation violates a business rule.
    """

    default_message = "This action violates a business rule."
    default_code = "business_rule_violation"


class ResourceNotOwned(ApplicationError):
    """
    Raised when a user attempts to access a resource
    owned by another user.
    """

    default_message = "You do not have permission to access this resource."
    default_code = "resource_not_owned"


class ExternalServiceError(ApplicationError):
    """
    Raised when an external dependency
    cannot successfully complete an operation.
    """

    default_message = "An external service is currently unavailable."
    default_code = "external_service_error"