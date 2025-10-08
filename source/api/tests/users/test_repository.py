import pytest

from app.database.session import RootSession
from app.users.repository import UserRepository


@pytest.fixture
def user_repository(test_session: RootSession):
    return UserRepository(test_session)


# @pytest.mark.integration
# def test_create_user(user_repository: UserRepository):
#     user = UserFactory.build(first_name="Ankur")
#     user_schema = CreateUser.model_validate(user)
#     created_user = user_repository.add(user_schema)
#     stored_user = user_repository.get(user.id)
#     assert created_user == stored_user
