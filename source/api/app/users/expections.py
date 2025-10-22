"""User exception module"""

from fastapi import status

from app.common.exceptions import AppBaseException, RaisableHTTPException
from app.common.schemas import ErrorDetail


class UserBaseException(AppBaseException):
    """User domain base exception."""


class UserNotFound(UserBaseException, RaisableHTTPException):
    """Unable to find a user."""


class UserNotAuthorized(UserBaseException):
    """Unable to authorize user"""


class UserNotAuthenticated(RaisableHTTPException):
    """Unable to authenticate user"""


class InvalidTokenError(RaisableHTTPException):
    def __init__(self, path: str):
        super().__init__(
            title="Invalid or expired token.",
            path=path,
            http_status_code=status.HTTP_401_UNAUTHORIZED,
            errors=[ErrorDetail(detail="JWT token is invalid or expired.")],
        )
