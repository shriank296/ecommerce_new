"""Low level methods for interacting with database.

"""

import logging
from typing import cast

from fastapi import Depends
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import RootSession
from app.database.manager import DatabaseManager
from app.settings import AppSettings, get_app_settings

logger = logging.getLogger(__name__)

_ENGINE: Engine | None = None


def _get_engine(app_settings: AppSettings) -> Engine:
    global _ENGINE

    logger.debug("Setting up a new database emgine.")

    if app_settings.IN_AZURE:
        pass
    else:
        connection_string = (
            f"postgresql://{app_settings.DB_USER}:{app_settings.DB_PASSWORD}"
            f"@{app_settings.DB_HOST}:{app_settings.DB_PORT}/{app_settings.DB_NAME}"
        )
    # There should be one connection used at one time. This then manages connections
    # to the database, including recycling and reusing connections. Without this we
    # end up forcing high connection usage at the DB which has significant memery overhead.

    if not _ENGINE:
        _ENGINE = create_engine(
            connection_string,
            # Main pool size
            pool_size=app_settings.APP_POOL_SIZE,
            # Overflow pool that is used if main pool is saturated.
            max_overflow=10,
            # Checkout a new connection with the DB after an connection
            # has been idle for more than 15 minutes.
            pool_recycle=900,
            # timeout time for waiting to create a new connection within
            # the pool. If this is exceeded a Timeout is thrown.
            pool_timeout=5,
            # This is required for the token refresh to fire on every connection.
            pool_pre_ping=True,
            # Use the 2.0 API.
            future=True,
        )
    return _ENGINE


def get_engine(
    app_settings: AppSettings = Depends(get_app_settings),
) -> Engine:
    """Get the active database engine.

    Args:
        None

    Returns:
        App database engine.
    """
    return _get_engine(app_settings)


def _get_database_session(engine: Engine) -> RootSession:
    """Create a new database session from an engine.

    Args:
        engine: SQLAlchemy engine to create session on.

    Returns:
        RootSession object.
    """
    logger.debug("Setting up a new local sessionmaker.")

    _session_maker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = cast(RootSession, _session_maker())

    return session


def get_database_session(engine: Engine = Depends(get_engine)) -> RootSession:
    return _get_database_session(engine)


def session_manager(session: RootSession) -> DatabaseManager:
    """Return our session manager.
    Session mamanger comes preconfigured with all available repositories. The
    session manager is configured as a context manager which will start
    Args:
        session: SQLAlchemy session to create manager for.
    Returns:
        SQLAlchemyManager object.
    """
    return DatabaseManager(session)
