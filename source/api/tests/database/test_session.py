"""Test our database fixtures work."""

from unittest.mock import Mock, call

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.manager import DatabaseManager
from app.database.session import RootSession, session_manager


@pytest.mark.integration
def test_root_session(test_session: RootSession):
    return test_session.execute(text("select 1 + 1")).scalars().one() == 2


def test_session_manager_commits_and_closes_if_no_exception_raised(
    test_session: RootSession,
) -> None:
    mock_session = Mock()
    mock_session.commit = Mock()
    with session_manager(mock_session) as db:
        db.commit()
        pass
    expected = [call.commit(), call.close()]
    mock_session.mock_calls == expected


def test_session_manager_raises_exception_and_rolls_back_and_closes_if_exception_raised() -> (
    None
):
    mock_session = Mock()
    mock_session.commit = Mock(side_effect=SQLAlchemyError)
    with pytest.raises(SQLAlchemyError):
        with session_manager(mock_session) as _:
            raise SQLAlchemyError
    expected = [call.rollback(), call.close()]
    assert mock_session.mock_calls == expected


def test_database_context_manager_commits_and_closes_if_no_exception_raised() -> None:
    mock_session = Mock()
    mock_session.commit = Mock()
    with DatabaseManager(mock_session) as _:
        pass

    expected = [call.close()]
    assert mock_session.mock_calls == expected


def test_database_context_manager_raises_exception_and_rolls_back_and_closes_if_exception_raised() -> (
    None
):
    mock_session = Mock()
    mock_session.commit = Mock(side_effect=SQLAlchemyError("Test Error"))
    with pytest.raises(Exception):
        with DatabaseManager(mock_session) as _:
            raise Exception("Test exception")

    expected = [call.rollback(), call.close()]
    assert mock_session.mock_calls == expected
