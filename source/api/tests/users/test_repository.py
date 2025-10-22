import pytest

from app.database.session import RootSession
from app.users.repository import UserRepository
from app.users.schemas import CreateUser
from tests.users.fixtures import UserFactory


@pytest.mark.integration
def test_create_user(user_repository: UserRepository):
    user = UserFactory.build(first_name="Ankur")
    user_schema = CreateUser.model_validate(user)
    created_user = user_repository.add(user_schema, flush=True)
    stored_user = user_repository.get(created_user.id)
    assert stored_user._password != user_schema.password
    assert stored_user.verify_password(user_schema.password)
    assert stored_user.first_name == user_schema.first_name


@pytest.mark.integration
def test_get_user(test_session: RootSession, user_repository: UserRepository):
    user = UserFactory.create()
    stored_user = user_repository.get(user.id)
    assert stored_user.id == user.id
    assert stored_user.email == user.email
