"""
Custom DRF exception handler for uniform API error responses.
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied as DRFPermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Convert exceptions into a standardised JSON error envelope:

    {
        "success": false,
        "message": "<human-readable summary>",
        "errors": { ... }   # field-level errors when available
    }
    """
    # Translate Django core exceptions into DRF equivalents.
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = DRFPermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception – return a generic 500.
        logger.exception("Unhandled exception in view %s", context.get("view"))
        return Response(
            {
                "success": False,
                "message": "An internal server error occurred. Please try again later.",
                "errors": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_detail = response.data

    if isinstance(error_detail, list):
        message = " ".join(str(e) for e in error_detail)
        errors = {}
    elif isinstance(error_detail, dict):
        if "detail" in error_detail:
            message = str(error_detail["detail"])
            errors = {}
        else:
            message = _extract_first_message(error_detail)
            errors = _flatten_errors(error_detail)
    else:
        message = str(error_detail)
        errors = {}

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }

    return response


def _extract_first_message(error_dict: dict) -> str:
    """Return the first human-readable error message from a nested error dict."""
    for value in error_dict.values():
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, dict):
            return _extract_first_message(value)
        return str(value)
    return "Validation error."


def _flatten_errors(error_dict: dict, prefix: str = "") -> dict:
    """Flatten nested error dicts to ``field: [messages]`` format."""
    result = {}
    for key, value in error_dict.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_errors(value, prefix=full_key))
        elif isinstance(value, list):
            result[full_key] = [str(e) for e in value]
        else:
            result[full_key] = [str(value)]
    return result


class BusinessLogicError(APIException):
    """Raise for domain-level errors that should surface as 400 Bad Request."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A business logic error occurred."
    default_code = "business_logic_error"


class ConflictError(APIException):
    """409 Conflict."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred."
    default_code = "conflict"


class PaymentError(APIException):
    """Payment-related errors."""

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "A payment error occurred."
    default_code = "payment_error"
