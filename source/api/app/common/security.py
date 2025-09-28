from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from jose import jwt


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

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
