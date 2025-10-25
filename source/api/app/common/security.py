import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import wraps
from typing import cast

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # type: ignore[import]

from app.database import RootSession
from app.database.session import get_database_session, session_manager
from app.settings import get_app_settings
from app.users.expections import InvalidTokenError, UserNotAuthorized

app_settings = get_app_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token/")

logger = logging.getLogger(__name__)


class TokenService(ABC):
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    @abstractmethod
    def create_token(
        self, user_name: str, role: str, expires_delta: timedelta | None = None
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def decode_token(self, token: str) -> dict:
        raise NotImplementedError


class JWTTokenService(TokenService):
    def __init__(self, secret_key: str, algorithm: str):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self, user_name: str, role: str, expires_delta=None, *args, **kwargs
    ):
        to_encode: dict[str, str | int] = {"sub": user_name, "role": role}
        expire = datetime.now() + (expires_delta or timedelta(minutes=30))
        to_encode.update({"exp": int(expire.timestamp())})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict[str, str]:
        decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        return cast(dict[str, str], decoded)


token_service = JWTTokenService(
    algorithm=app_settings.ALGORITHM, secret_key=app_settings.SECRET_KEY
)


def get_token_service() -> TokenService:
    """Returns singleton JWT service instance for FASTAPI routes."""
    return token_service


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    token_service: TokenService = Depends(get_token_service),
    db_session: RootSession = Depends(get_database_session),
):
    try:
        payload = token_service.decode_token(token)
        user_name: str | None = payload.get("sub")
        role: str | None = payload.get("role")

        if not user_name or not role:
            logger.warning("Invalid token payload: missing sub or role.")
            raise InvalidTokenError(path=request.url.path)
        with session_manager(db_session) as uow:
            user = uow.users.get_one(uow.users.model.email == user_name)
        if not user:
            raise InvalidTokenError(path=request.url.path)

        # Return user info (or fetch from DB if needed)
        return {"user_name": user_name, "role": role}

    except JWTError:
        logger.warning(f"JWT decoding failed for {request.url.path}")
        raise InvalidTokenError(path=request.url.path)


def require_role(role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise UserNotAuthorized
            if current_user.get("role") == role:
                return func(*args, **kwargs)
            raise UserNotAuthorized

        return wrapper

    return decorator
