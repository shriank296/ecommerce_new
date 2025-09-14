import logging
from types import TracebackType
from typing import Protocol, Self, overload

from sqlalchemy.exc import SQLAlchemyError

from app.database import RootSession
from app.users.protocols import UserProtocol
from app.users.repository import UserRepository

logger = logging.getLogger(__name__)


class DatabaseManagerProtocol(Protocol):
    """Database session manager protocol."""

    def __init__(self, session: RootSession): ...

    def __enter__(self) -> Self: ...

    @overload
    def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None: ...

    @overload
    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def flush(self) -> None: ...

    @property
    def users(self) -> UserProtocol: ...


class DatabaseManager:
    """Unit of work style manager which provides high level DB access."""

    def __init__(self, session: RootSession):
        self._session: RootSession = session

    def __enter__(self) -> Self:
        self.users = UserRepository(session=self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            logger.warning("no active session found during context exit")

        try:
            if exc_type is not None:
                self.rollback()
                logger.warning(
                    "Rolling back transaction due to exception",
                    exc_info=True,
                )
        except SQLAlchemyError as e:
            logger.error(
                f"database error during session cleanup: {str(e)}", exc_info=True
            )
            raise
        finally:
            self.close()

    def commit(self) -> None:
        """Commit all changes in current session."""
        logger.debug("Committing batabase transaction")
        self._session.commit()

    def rollback(self):
        """Rollback all changes in the current session."""
        logger.debug("Rolling back batabase transaction")
        self._session.rollback()

    def close(self):
        """Close current database session."""
        logger.debug("CLosing database session")
        self._session.close()

    def flush(self):
        """Flush current session changes to database.

        This can be useful in cases where you want to populate keys used
        is declaring relationships.

        """
        logger.debug("Flushing session to DB")
        self._session.flush()
