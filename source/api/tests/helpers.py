from collections.abc import Callable
from types import TracebackType
from typing import Generic, Self, TypeVar

import jwt
from pydantic import PostgresDsn

T = TypeVar("T")


class LazyLoader(Generic[T]):
    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._instance: T | None = None

    def value(self) -> T:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance

    def override(self, value: T) -> None:
        self._instance = value


def build_postgres_dsn(
    host: str,
    port: str,
    user: str,
    password: str,
    dbname: str,
    scheme: str = "postgresql",
    **kwargs: str | int,
) -> str:
    """Build a postgres DSN from component parts."""
    return str(
        PostgresDsn.build(
            scheme="postgresql",
            host=host,
            port=int(port),
            password=password,
            path=dbname,
        )
    )


class BaseTestingSessionManager:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def flush(self) -> None:
        pass


def make_jwt_token(roles: list[str]) -> str:
    """Encode a JWT with the given roles list"""
    payload = {"roles": roles}
    token = jwt.encode(payload, key="", algorithm="none")
    return f"Bearer {token}"
