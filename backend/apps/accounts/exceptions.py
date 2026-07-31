"""
Account-specific application exceptions.
"""

from apps.core.exceptions import ApplicationError


class UserAlreadyExists(ApplicationError):
    """
    Raised when attempting to register an email address
    that already exists.
    """

    message = "A user with this email already exists."
    code = "user_already_exists"


class InvalidCredentials(ApplicationError):
    """
    Raised when login credentials are invalid.
    """

    message = "Invalid email or password."
    code = "invalid_credentials"


class InactiveAccount(ApplicationError):
    """
    Raised when an inactive user attempts authentication.
    """

    message = "This account is inactive."
    code = "inactive_account"