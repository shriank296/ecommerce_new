"""Shared pydantic schema utilities"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelMode(BaseModel):
    """Base model that uses cameCase aliases and supports ORM mode."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorDetail(BaseModel):
    """Represents a single, human-readable error message.

    This model is typically used to provide additional context
    about what went wrong, such as validation failures or
    domain-specific business logic errors.
    """

    detail: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ErrorResponse(BaseModel):
    """Standardized error response model returned by the API.

    This model ensures that all errors follow a consistent
    structure, making it easier for clients to handle them.

    Attributes:
        timestamp: The time when the error occurred (UTC).
        status: The HTTP status code associated with the error.
        title: A short, human-readable summary of the error.
        path: The request path where the error occurred.
        errors: A list of detailed error messages (if any).
    """

    timestamp: datetime
    status: int
    title: str
    path: str
    errors: list[ErrorDetail]


class ApimResponse(CamelMode):
    """Standard API response model for successful operations.

    This model provides a consistent response structure across
    the application, ensuring clients can reliably parse results.

    Attributes:
        status_code: The HTTP status code representing the result
            of the request (e.g., 200 for success).
        message: A short, human-readable description of the result
            (e.g., "User created successfully").
    """

    status_code: int
    message: str
