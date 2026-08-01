"""
Global DRF exception handler.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.core.exceptions import ApplicationError


def custom_exception_handler(exc, context):
    """
    Global exception handler for the API.

    Handles both:

    - Django REST Framework exceptions.
    - Application-level exceptions raised by the service layer.
    """

    if isinstance(
        exc,
        ApplicationError,
    ):
        return Response(
            {
                "success": False,
                "errors": {
                    "message": exc.message,
                    "code": exc.code,
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = exception_handler(
        exc,
        context,
    )

    if response is None:
        return response

    response.data = {
        "success": False,
        "errors": response.data,
    }

    return response