"""
Global DRF exception handler.
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default exception handler to provide a
    consistent response structure.
    """

    response = exception_handler(exc, context)

    if response is None:
        return response

    response.data = {
        "success": False,
        "errors": response.data,
    }

    return response