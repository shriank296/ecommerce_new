import logging
from datetime import datetime, timezone
from enum import StrEnum
from functools import cache

from azure.servicebus.exceptions import ServiceBusError
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from psycopg2.errors import OperationalError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.common import exceptions as E
from app.common.schemas import ErrorDetail, ErrorResponse
from app.users.expections import UserNotAuthorized

logger = logging.getLogger(__name__)


class ErrorTypeEnum(StrEnum):
    MANDATORY_FIELD_MISSING = "Missing attribute"
    INVALID_DATA = "Invalid attribute"


ERROR_TYPE_MAPPING = {
    ErrorTypeEnum.MANDATORY_FIELD_MISSING.value: ["missing"],
    ErrorTypeEnum.INVALID_DATA.value: [
        "string_pattern_mismatch",
        "value_error",
        "greater_than",
        "date_from_datetime_inexact",
        "date_from_datetime_parsing",
        "date_future",
        "date_parsing",
        "date_past",
        "date_type",
        "datetime_from_date_parsing",
        "datetime_future",
        "datetime_object_invalid",
        "datetime_parsing",
        "datetime_past",
        "datetime_type",
        "assertion_error",
        "bool_parsing",
        "bool_type",
        "bytes_too_long",
        "bytes_too_short",
        "bytes_type",
        "enum",
        "arguments_type",
        "bytes_invalid_encoding",
        "decimal_max_digits",
        "decimal_max_places",
        "decimal_parsing",
        "list_type",
        "uuid_type",
        "uuid_parsing",
        "uuid_version",
    ],
}


@cache
def get_error_type_mapping_by_message() -> dict[str, str]:
    """Get the error type mapping by message.

    Returns:
        dict[str, str]: A dictionary mapping error messages to their corresponding types.
    """
    return {v: k for k, values in ERROR_TYPE_MAPPING.items() for v in values}


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.debug("Handling validation exception.")
    errors = []
    ERROR_TYPE_MAPPING_BY_MESSAGE = get_error_type_mapping_by_message()
    for error in exc.errors():
        attribute = error["loc"][-1]
        logger.debug(f"Validation error: {str(error)}")
        error_message = f"{ERROR_TYPE_MAPPING_BY_MESSAGE.get(error['type'], error['msg'])} '{attribute}'"
        errors.append(ErrorDetail(detail=error_message))
    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Invalid request payload",
        errors=errors,
        path=request.url.path,
    ).model_dump()
    return JSONResponse(
        jsonable_encoder(body), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def generic_exception_handler(
    request: Request, exc: E.RaisableHTTPException
) -> JSONResponse:
    logger.debug("Handling using generic error handler.")
    http_status_code = (
        exc.http_status_code if exc.http_status_code else status.HTTP_200_OK
    )
    logger.debug(
        "Handling error",
        extra={"status_code": exc.http_status_code, "error": exc.title},
    )
    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status_code,
        title=exc.title,
        errors=exc.errors,
        path=exc.path,
    ).model_dump()
    return JSONResponse(jsonable_encoder(body), status_code=http_status_code)


def server_unavailable_handler(request: Request, exc: OperationalError) -> JSONResponse:
    logger.debug("Handling 503 error.")
    title = "Server unavailable, retry later."
    http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    logger.error(
        "Server unavailable error",
        extra={"status_code": http_status_code, "error": title},
    )
    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status_code,
        title=title,
        errors=[ErrorDetail(detail="Check /status")],
        path=request.url.path,
    ).model_dump()
    return JSONResponse(jsonable_encoder(body), status_code=http_status_code)


def method_not_allowed_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle method not allowed exceptions."""
    logger.debug("Handling method not allowed error.")
    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
        title="Method Not Allowed",
        errors=[
            ErrorDetail(
                detail=f"Method '{request.method}' is not allowed for this endpoint."
            )
        ],
        path=request.url.path,
    ).model_dump()
    return JSONResponse(
        jsonable_encoder(body), status_code=status.HTTP_405_METHOD_NOT_ALLOWED
    )


def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.debug("Handling integrity error.")
    http_status_code = status.HTTP_409_CONFLICT
    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status_code,
        title="Integrity Error",
        errors=[ErrorDetail(detail="Resource already exists or violates constraints")],
        path=request.url.path,
    ).model_dump()
    return JSONResponse(jsonable_encoder(body), status_code=http_status_code)


def rbac_error_handler(request: Request, exc: UserNotAuthorized) -> JSONResponse:
    logger.warning(
        f"RBAC violation: user not authorized for {request.method} {request.url.path}"
    )

    http_status_code = status.HTTP_403_FORBIDDEN

    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status_code,
        title="Forbidden",
        errors=[ErrorDetail(detail="User is not authorized to perform this action.")],
        path=request.url.path,
    ).model_dump()

    return JSONResponse(content=jsonable_encoder(body), status_code=http_status_code)


def servicebus_exception_handler(
    request: Request, exc: ServiceBusError
) -> JSONResponse:
    """Handle Service Bus-related errors."""
    logger.debug("Handling ServiceBusError exception.")

    title = "Failed to communicate with Azure Service Bus."
    http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Try to capture the specific error message from the SDK
    detail_msg = str(exc) or "Service Bus operation failed."

    logger.error(
        "Service Bus error",
        extra={
            "status_code": http_status_code,
            "error": title,
            "exception_type": type(exc).__name__,
            "exception_detail": detail_msg,
        },
    )

    body = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status_code,
        title=title,
        errors=[ErrorDetail(detail=detail_msg)],
        path=request.url.path,
    ).model_dump()

    return JSONResponse(jsonable_encoder(body), status_code=http_status_code)
