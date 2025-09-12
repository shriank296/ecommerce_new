"""Common exceptions."""

from app.common.schemas import ErrorDetail


class AppBaseException(Exception):
    """Generic base exception for all App exceptions."""


class RaisableHTTPException(AppBaseException):
    """Can be used to raise a specific HTTP status code.

    THis is intended to be used within business logic to
    raise exception and return a specific error code. This is
    then caught within `main.py` at the top level and handled.
    This removes the need to have custom error handling logic
    in either the view or the router.
    """

    def __init__(
        self,
        title: str,
        path: str,
        http_status_code: int,
        errors: list[ErrorDetail] | None = None,
    ) -> None:
        """Initialize a new RaisableHTTPException.

        Args:
            title: A short, human-readable description of the error
                (e.g., "User not found").
            path: The request path where the error occurred
                (e.g., "/users/123").
            http_status_code: The HTTP status code to return with
                this error (e.g., 400, 404, 500).
            errors: Optional list of detailed error messages providing
                additional context (e.g., validation failures).
        """
        self.title = title
        self.path = path
        self.http_status_code = http_status_code
        self.errors = errors if errors else []
        super().__init__(title)
