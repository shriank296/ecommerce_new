"""General database tools meant for testing."""

from collections.abc import Callable, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.expression import ColumnExpressionArgument

T = TypeVar("T")

OrmType = TypeVar("OrmType", bound=DeclarativeBase)
DTOType = TypeVar("DTOType", bound=BaseModel)


class FakeRepository(Generic[OrmType, DTOType]):
    """A Generic in-memory repository for unit testing.

    Stores a collection of ORM-like model instances and provides basic CRUD-style
    operations. Intended for use as a test double for repository protocols.

    Example usage:
        repo = FakeRepository[UserModel, UserSchema](
        create_model_fn=lambda schema: UserModel(**schema.model_dump())
    )
    user = repo.add(UserSchema(name="Alice"))
    fetched = repo.get(1)
    all_users = repo.list()

    Type Args:
        OrmType: The ORM model type to store in the repository.
        DTOType: The Pydantic scheme or DTO type used as input for creation.

    Attributes:
        results: In memory list of stored model instances.
        Create_model_fn:
            Optional function used to convert an input schema into the corresponding
            ORM model instance when calling `add`. If not provided, `add` will raise
            NotImplementedError.
    """

    def __init__(
        self,
        results: list[OrmType] | None = None,
        create_model_fn: Callable[[DTOType], OrmType] | None = None,
    ):
        self._results: list[OrmType] = [] if results is None else results
        self.create_model_fn = create_model_fn

    def get(self, pk: Any) -> OrmType | None:
        """Return the first stored model if any exist, else None.

        Ignores the ID argument is this fake implementation.

        Args:
            pk: unused.

        Returns:
            First record in stored results, or None if none are stored yet.
        """
        return None if not self._results else self._results[0]

    def list(self, *args: ColumnExpressionArgument[bool]) -> Sequence[OrmType]:
        """Return all stored models in the repository

        Args:
            args: variable number of filter args.

        Returns:
            All stored results, regardless of filter.
        """
        return self._results

    def add(self, input_model: DTOType) -> OrmType:
        """Add a record in the memory results.

        Args:
            input_model: this will be transformed using the `create_model_fn`
                callable. That value will then be stored in the results list.

        Returns:
            Output
        """
        if self.create_model_fn is None:
            raise NotImplementedError("No create_model_fn in this repository.")
        db_model = self.create_model_fn(input_model)
        self._results.append(db_model)
        return db_model

    def delete(self, *args: ColumnExpressionArgument[bool]) -> int:
        """Returns 1 and clears saved results"""
        self._results.clear()
        return 1

    def update(
        self,
        conditions: Sequence[ColumnExpressionArgument[bool]],
        input_values: dict[str, Any],
    ) -> Sequence[OrmType]:
        """Returns all stored resultsm these are unchanged."""
        return self._results
