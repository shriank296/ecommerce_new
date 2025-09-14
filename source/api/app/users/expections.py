"""User exception module"""

from app.common.exceptions import AppBaseException, RaisableHTTPException


class UserBaseException(AppBaseException):
    """User domain base exception."""


class UserNotFound(UserBaseException, RaisableHTTPException):
    """Unable to find a user."""
