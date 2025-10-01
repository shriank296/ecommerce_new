import logging
import random
from collections.abc import Generator
from contextlib import contextmanager
from enum import Enum
from typing import cast

import factory
import pytest
from faker import Faker
from pydantic import BaseModel
from sqlalchemy import String, create_engine, delete, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.database.repository import BaseRepository
from app.database.session import RootSession

logger = logging.getLogger(__name__)
faker = Faker()


@pytest.fixture(scope="session")
def dummy_session():
    # Create a temporary engine
    engine = create_engine(
        "sqlite://",
        echo=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    return cast(RootSession, session)


class Base(DeclarativeBase):
    pass


class Potato(Enum):
    RAW = "raw"
    COOKED = "cooked"
    MASHED = "mashed"
    FONDANT = "fondant"
    SMOOTHIE = "smoothie"


class DummyTable(Base):
    __tablename__ = "testings"
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(50))
    value: Mapped[int]
    potato: Mapped[Potato]


class DummyTableFactory(factory.base.BaseFactory[DummyTable]):
    """Factory for creating 'Dummy' objects."""


@pytest.fixture(scope="session")
def dummy_table_factory(
    dummy_session: RootSession,
) -> Generator[DummyTableFactory, None, None]:
    with dummy_table_builder(dummy_session) as result:
        yield result

    # Clean the table after every call.
    dummy_session.execute(delete(DummyTable))


@contextmanager
def dummy_table_builder(
    dummy_session: RootSession,
) -> Generator[DummyTableFactory, None, None]:
    class _DummyTableFactory(factory.alchemy.SQLAlchemyModelFactory, DummyTableFactory):
        """
        Creates a random object (as can be seen in the body of this class)
        and writes it in the db using the Meta class data
        More info here
        https://factoryboy.readthedocs.io/en/stable/orms.html#factory.alchemy.SQLAlchemyModelFactory
        """

        id = factory.Sequence(lambda n: n)
        company = factory.LazyFunction(lambda: str(faker.company()))
        value = factory.LazyFunction(lambda: random.randint(0, 1000))
        potato = factory.LazyFunction(lambda: random.choice([x for x in Potato]))

        class Meta:
            model = DummyTable
            sqlalchemy_session = dummy_session
            sqlalchemy_session_persistence = "commit"

    yield cast(DummyTableFactory, _DummyTableFactory)


class DummyTableDTO(BaseModel):
    id: int
    company: str
    value: int
    potato: Potato


# Dummy class for reads/writes in a Dummy model
class DummyTableRepository(BaseRepository[DummyTable, int, DummyTableDTO]):
    model = DummyTable


@pytest.fixture
def dummy_repository(dummy_session: RootSession) -> DummyTableRepository:
    return DummyTableRepository(session=dummy_session)


@pytest.mark.integration
def test_repository_get(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:

    # Create an object in the DB.
    dummy_obj = dummy_table_factory.create()
    # Fetch it out using our repo.
    stored_obj = dummy_repository.get(dummy_obj.id)

    assert dummy_obj == stored_obj


@pytest.mark.integration
def test_repository_add_get(dummy_repository: DummyTableRepository) -> None:
    new_dummy_object = DummyTableDTO(
        id=37182, company="Kostas LTD", value=3, potato=Potato.COOKED
    )
    added_object = dummy_repository.add(new_dummy_object)
    returned_obj = dummy_repository.get(new_dummy_object.id)
    assert returned_obj == added_object


@pytest.mark.integration
def test_repository_list_all(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:
    # Create
    created_objs = dummy_table_factory.create_batch(3)

    # Retrieve
    retrieve_object = dummy_repository.list()

    # Check
    assert set(created_objs).issubset(retrieve_object)


@pytest.mark.integration
def test_repository_list_args(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:
    # Create
    dummy_obj = dummy_table_factory.create_batch(2)

    # Retrieve one
    expression = DummyTable.id == dummy_obj[0].id
    list_object = dummy_repository.list(expression)

    # Check
    assert list_object[0] == dummy_obj[0]

    # Retrieve two
    expression = or_(DummyTable.id == dummy_obj[0].id, DummyTable.id == dummy_obj[1].id)
    list_object = dummy_repository.list(expression)

    # Check
    assert set([dummy_obj[0], dummy_obj[1]]).issubset(set(list_object))


@pytest.mark.integration
def test_repository_delete(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:

    QUANTITY = 5
    # Create
    dummy_obj = dummy_table_factory.create_batch(QUANTITY)

    # Delete
    condition = [DummyTable.id == a.id for a in dummy_obj]
    expression = or_(*condition)

    # Note:
    # > print(expression)
    # testings.id = :id_1 OR testings.id = :id_2 OR testings.id = :id_3 OR ...

    num_of_deleted = dummy_repository.delete(expression)
    assert num_of_deleted == QUANTITY


@pytest.mark.integration
def test_repository_update(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:
    # Create
    dummy_obj = dummy_table_factory.create()

    conditions = [DummyTable.id == dummy_obj.id]

    input_value = {"company": "Ankur LTD", "value": 4}

    updated_res = dummy_repository.update(conditions, input_value)

    assert updated_res[0].company == "Ankur LTD"


@pytest.mark.integration
def test_repository_update_multiple(
    dummy_repository: DummyTableRepository, dummy_table_factory: DummyTableFactory
) -> None:

    QUANTITY = 3
    # Create multiple
    _ = dummy_table_factory.create_batch(QUANTITY, value=20)
    dummy_obj_2 = dummy_table_factory.create_batch(QUANTITY, value=10)

    conditions = [DummyTable.value == 20]

    input_values = {"value": 25}

    updated_obj = dummy_repository.update(conditions, input_values)

    assert len(updated_obj) == QUANTITY

    # check that we did not accidently update wrong objects

    condition = [DummyTable.id == a.id for a in dummy_obj_2]
    expression = or_(*condition)

    returned_obj = dummy_repository.list(expression)

    assert QUANTITY == len([a.value == 20 for a in returned_obj])
