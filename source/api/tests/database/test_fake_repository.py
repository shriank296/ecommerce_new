from typing import Any

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

from tests.database import FakeRepository


class UserSchema(BaseModel):
    name: str


class FakeRepositoryBase(DeclarativeBase):
    """This is just for testing"""


class User(FakeRepositoryBase):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __eq__(self, obj: Any):
        return True if obj.id == self.id and obj.name == self.name else False


@pytest.fixture(scope="function")
def fake_repo() -> FakeRepository:
    """Fixture to provide a FakeRepository for User.

    This is a function scope and reset for every test.
    """

    def create_user(schema: UserSchema) -> User:
        return User(id=1, name=schema.name)

    return FakeRepository[User, UserSchema](create_model_fn=create_user)


def test_add_stores_object(fake_repo: FakeRepository) -> None:
    NAME = "Alice"
    schema = UserSchema(name=NAME)
    user = fake_repo.add(schema)

    assert isinstance(user, User)
    assert user.name == NAME
    assert fake_repo._results == [User(id=1, name=NAME)]


def test_list_returns_all_objects(fake_repo: FakeRepository) -> None:
    fake_repo._results = [User(id=1, name="Alice"), User(id=2, name="Bob")]

    all_users = fake_repo.list()

    assert len(all_users) == 2
    assert all_users[0].name == "Alice"
    assert all_users[1].name == "Bob"


def test_get_returns_first_object(fake_repo: FakeRepository) -> None:
    fake_repo.add(UserSchema(name="Dave"))
    fetched = fake_repo.get(1)

    assert fetched is not None
    assert fetched.name == "Dave"


def test_get_returns_none_if_empty() -> None:
    fake_repo = FakeRepository[User, UserSchema](
        create_model_fn=lambda s: User(id=1, name=s.name)
    )
    assert fake_repo.get(1) is None


def test_delete_returns_1(fake_repo: FakeRepository) -> None:
    fake_repo.add(UserSchema(name="Alice"))

    result = fake_repo.delete()

    assert result == 1
    assert fake_repo._results == []


def test_update_returns_results(fake_repo: FakeRepository) -> None:
    fake_repo.add(UserSchema(name="Dev"))

    updated = fake_repo.update([], {})

    assert len(updated) == 1
    assert fake_repo._results == [User(id=1, name="Dev")]


def test_add_raises_if_no_create_fn() -> None:
    fake_repo = FakeRepository[User, UserSchema]()
    with pytest.raises(NotImplementedError):
        fake_repo.add(UserSchema(name="Bob"))
