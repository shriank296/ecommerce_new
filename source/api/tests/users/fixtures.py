import random

import factory
import pytest

from app.database.session import RootSession
from app.users.models import User, UserRole
from app.users.repository import UserRepository
from tests.fixtures import faker, lazy_session


# Repository
@pytest.fixture
def user_repository(test_session: RootSession) -> UserRepository:
    return UserRepository(test_session)


# Factory
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    id = factory.LazyAttribute(lambda _: faker.uuid4())
    first_name = factory.LazyFunction(lambda: faker.first_name())
    last_name = factory.LazyFunction(lambda: faker.last_name())
    email = factory.LazyAttribute(lambda obj: f"{obj.first_name}@example.com")
    password = factory.LazyFunction(lambda: faker.password(12))
    phone = factory.Faker("msisdn")
    address = factory.LazyFunction(
        lambda: {
            "street": faker.street_address(),
            "city": faker.city(),
            "zip": faker.zipcode(),
            "country": faker.country(),
        }
    )
    role = factory.LazyFunction(lambda: random.choice(list(UserRole)))
    created_by = factory.LazyFunction(lambda: faker.user_name())
    updated_by = factory.LazyFunction(lambda: faker.user_name())

    class Meta:
        model = User
        sqlalchemy_session_factory = lazy_session.value
        sqlalchemy_session_persistence = "commit"
